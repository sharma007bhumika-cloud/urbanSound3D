"""
Acoustic Propagation Engine (Simplified ISO 9613-2 Framework).
Vectorized simulation of outdoor sound propagation over urban terrain.

Key Formula:
L_receiver = L_source + D_c - (A_div + A_atm + A_gr + A_bar + A_misc)
L_total = 10 * log10(sum(10^(L_i / 10)))

Academic Disclaimer:
This is an educational engineering model designed for academic simulation and comparative
planning analysis. It is not a certified regulatory tool.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from shapely.geometry import Point, LineString, Polygon
from shapely.strtree import STRtree

from core.sources import NoiseSource
from core.geometry import Building, SoundBarrier, CityLayout

def calculate_atmospheric_alpha(temp_c: float = 20.0, rel_humidity: float = 50.0) -> float:
    """
    Computes atmospheric attenuation coefficient alpha (dB/km) at 500 Hz broadband equivalent.
    Standard baseline: 20°C, 50% RH yields ~1.9 dB/km.
    Varies smoothly with temperature and humidity based on ISO 9613-1 approximation.
    """
    t = np.clip(temp_c, -10.0, 50.0)
    rh = np.clip(rel_humidity, 10.0, 100.0)
    # Empirical smooth surface around 1.9 dB/km
    alpha = 1.9 * (1.0 + 0.018 * (20.0 - t)) * (1.0 + 0.008 * (50.0 - rh))
    return float(np.clip(alpha, 0.5, 8.0))


def compute_ground_attenuation(
    d: np.ndarray,
    ground_type: str = "mixed",
    z_s: float = 0.8,
    z_r: float = 1.5
) -> np.ndarray:
    """
    Non-negative ground absorption term A_gr (dB).
    - Hard ground (asphalt, concrete): G = 0.0 (minimal ground absorption)
    - Mixed ground (suburban): G = 0.5
    - Soft ground (lawns, parkland): G = 1.0 (strong porous absorption)
    """
    g_map = {"hard": 0.0, "mixed": 0.5, "grass": 1.0, "soft": 1.0}
    G = g_map.get(ground_type.lower(), 0.5)
    
    # Distance scale factor and height dampening
    dist_factor = 1.0 - np.exp(-d / 50.0)
    height_factor = 1.0 / (1.0 + 0.25 * (z_s + z_r))
    a_gr = G * 4.5 * dist_factor * height_factor
    return np.maximum(a_gr, 0.0)


def check_ray_intersection_2d(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    segments: List[Tuple[Tuple[float, float], Tuple[float, float]]]
) -> bool:
    """Returns True if ray segment p1->p2 intersects any segment in the list."""
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1

    for seg in segments:
        (sx1, sy1) = seg[0]
        (sx2, sy2) = seg[1]
        sdx = sx2 - sx1
        sdy = sy2 - sy1
        denom = dx * sdy - dy * sdx
        if abs(denom) < 1e-9:
            continue
        t = ((sx1 - x1) * sdy - (sy1 - y1) * sdx) / denom
        u = ((sx1 - x1) * dy - (sy1 - y1) * dx) / denom
        if 0.001 <= t <= 0.999 and 0.0 <= u <= 1.0:
            return True
    return False


def build_obstacle_segments(
    buildings: List[Building],
    barriers: List[SoundBarrier]
) -> List[Tuple[Tuple[float, float], Tuple[float, float], float]]:
    """
    Extracts all 2D obstacle segments with their effective heights (sx1, sy1, sx2, sy2, height).
    """
    segments = []
    # Barrier walls
    for b in barriers:
        segments.append(((b.x1, b.y1), (b.x2, b.y2), b.height))
        
    # Building perimeter walls
    for bld in buildings:
        coords = list(bld.polygon.exterior.coords)
        for i in range(len(coords) - 1):
            segments.append((coords[i], coords[i+1], bld.height))
            
    return segments


def compute_barrier_attenuation_grid(
    src_x: float,
    src_y: float,
    src_z: float,
    X_grid: np.ndarray,
    Y_grid: np.ndarray,
    rec_z: float,
    buildings: List[Building],
    barriers: List[SoundBarrier]
) -> np.ndarray:
    """
    Fast vectorized building & sound barrier screening attenuation A_bar (dB).
    Implements Kurze-Anderson / Maekawa path difference formulation capped at 20 dB.
    Uses bounding-box ray intersection tests in vectorized NumPy for real-time speed.
    """
    ny, nx = X_grid.shape
    A_bar = np.zeros((ny, nx), dtype=np.float32)
    
    # Collect all barrier lines and building bounding boxes
    all_obstacles = []
    for b in barriers:
        all_obstacles.append({
            'type': 'barrier',
            'line': LineString([(b.x1, b.y1), (b.x2, b.y2)]),
            'height': b.height,
            'x_mid': 0.5 * (b.x1 + b.x2),
            'y_mid': 0.5 * (b.y1 + b.y2),
            'bounds': (min(b.x1, b.x2), min(b.y1, b.y2), max(b.x1, b.x2), max(b.y1, b.y2))
        })
    for bld in buildings:
        all_obstacles.append({
            'type': 'building',
            'polygon': bld.polygon,
            'height': bld.height,
            'x_mid': bld.centroid[0],
            'y_mid': bld.centroid[1],
            'bounds': bld.bounds
        })
        
    if not all_obstacles:
        return A_bar

    # For fast raster approximation:
    # A ray from source (src_x, src_y) to receiver (xr, yr) is intercepted if the ray cuts the obstacle.
    # We test obstacles whose bounding box overlaps the bounding box of (source, receiver).
    for obs in all_obstacles:
        bx1, by1, bx2, by2 = obs['bounds']
        h_obs = obs['height']
        
        # Grid points that could be shadowed by this obstacle
        # Ray direction: from source to receiver
        # Vector from source to obstacle centroid:
        ox = obs['x_mid'] - src_x
        oy = obs['y_mid'] - src_y
        dist_obs = np.sqrt(ox**2 + oy**2)
        if dist_obs < 1.0:
            continue
            
        # Angle span of the obstacle from source
        # Points behind obstacle have distance from source > dist_obs
        dx = X_grid - src_x
        dy = Y_grid - src_y
        d_rec = np.sqrt(dx**2 + dy**2) + 1e-6
        
        # Dot product / projection: receiver must be beyond the obstacle
        proj = (dx * ox + dy * oy) / (dist_obs + 1e-6)
        beyond_mask = proj > dist_obs
        
        if not np.any(beyond_mask):
            continue
            
        # Angular cross product to test if receiver lies within obstacle shadow wedge
        # Approximate angular half-width
        half_w = max(4.0, 0.5 * max(bx2 - bx1, by2 - by1))
        # Perpendicular distance of receiver line to obstacle center
        perp_dist = np.abs(dx * oy - dy * ox) / (dist_obs + 1e-6)
        
        # Shadow zone expands slightly with distance behind obstacle
        shadow_width = half_w * (1.0 + 0.15 * (proj - dist_obs) / dist_obs)
        shadow_mask = beyond_mask & (perp_dist < shadow_width)
        
        if np.any(shadow_mask):
            # Path difference delta calculation (Maekawa)
            # delta = d(source, top of barrier) + d(top of barrier, receiver) - d(direct)
            d1 = np.sqrt(dist_obs**2 + (h_obs - src_z)**2)
            d2 = np.sqrt((d_rec[shadow_mask] - dist_obs)**2 + (h_obs - rec_z)**2)
            d_direct = np.sqrt(d_rec[shadow_mask]**2 + (rec_z - src_z)**2)
            delta = np.maximum(0.0, d1 + d2 - d_direct)
            
            # Fresnel number N = 2 * delta / lambda (lambda = 0.68m at 500 Hz)
            N = 2.0 * delta / 0.68
            # Screening attenuation formula
            a_obs = 10.0 * np.log10(3.0 + 20.0 * N)
            a_obs = np.clip(a_obs, 5.0, 20.0)
            
            A_bar[shadow_mask] = np.maximum(A_bar[shadow_mask], a_obs)

    return np.clip(A_bar, 0.0, 20.0)


def simulate_grid(
    city: CityLayout,
    sources: List[NoiseSource],
    grid_res: int = 100,
    rec_height: float = 1.5,
    ground_type: str = "mixed",
    temp_c: float = 20.0,
    rel_humidity: float = 50.0,
    green_buffer: bool = False
) -> Dict[str, Any]:
    """
    Executes full vectorized noise simulation over a 2D spatial grid.
    Returns grid coordinates, individual source fields, and total energy-summed sound pressure level.
    """
    width = city.width
    height = city.height
    
    # Generate receiver grid coordinates
    x_coords = np.linspace(0.0, width, grid_res, dtype=np.float32)
    y_coords = np.linspace(0.0, height, grid_res, dtype=np.float32)
    X, Y = np.meshgrid(x_coords, y_coords)
    
    alpha = calculate_atmospheric_alpha(temp_c, rel_humidity)
    
    # Active sources
    active_sources = [s for s in sources if s.active]
    if not active_sources:
        # Return ambient silence (30 dB baseline)
        ambient = np.full_like(X, 30.0)
        return {
            "X": X, "Y": Y, "L_total": ambient, "grid_res": grid_res,
            "x_coords": x_coords, "y_coords": y_coords,
            "sources": sources, "city": city
        }
        
    energy_sum = np.zeros_like(X, dtype=np.float64)
    source_levels = []
    
    for s in active_sources:
        # Distance calculation
        dx = X - s.x
        dy = Y - s.y
        dz = rec_height - s.z
        d_3d = np.sqrt(dx**2 + dy**2 + dz**2)
        d_eff = np.maximum(d_3d, 1.0)
        
        # 1. Geometric Divergence A_div = 20*log10(d) + 11 (point source in free field)
        A_div = 20.0 * np.log10(d_eff) + 11.0
        
        # 2. Atmospheric Absorption A_atm = alpha * d / 1000
        A_atm = alpha * d_eff / 1000.0
        
        # 3. Ground Attenuation A_gr
        A_gr = compute_ground_attenuation(d_eff, ground_type, s.z, rec_height)
        
        # 4. Obstacle / Barrier Screening Attenuation A_bar
        A_bar = compute_barrier_attenuation_grid(
            s.x, s.y, s.z, X, Y, rec_height, city.buildings, city.barriers
        )
        
        # 5. Miscellaneous / Green Buffer Attenuation A_misc
        A_misc = np.zeros_like(X)
        if green_buffer:
            # Green belt adds up to 3-5 dB attenuation over 30m depth
            A_misc = np.clip(0.08 * d_eff, 0.0, 5.0)
            
        # Net Received Sound Pressure Level from this source
        # L_rec = Lw + D_c - (A_div + A_atm + A_gr + A_bar + A_misc)
        L_rec = s.lw - (A_div + A_atm + A_gr + A_bar + A_misc)
        
        # Add to total energy
        energy_sum += 10.0 ** (L_rec / 10.0)
        source_levels.append({
            "source": s,
            "L_rec": L_rec
        })
        
    # Baseline acoustic noise floor in urban atmosphere (~30 dB)
    energy_sum += 10.0 ** (30.0 / 10.0)
    L_total = 10.0 * np.log10(energy_sum)
    
    # Mask interior of buildings to highlight facades and streets
    for bld in city.buildings:
        bx1, by1, bx2, by2 = bld.bounds
        in_bbox = (X >= bx1) & (X <= bx2) & (Y >= by1) & (Y <= by2)
        # Slightly attenuate building roof interior to give realistic contrast
        L_total[in_bbox] = np.maximum(32.0, L_total[in_bbox] - 8.0)
        
    return {
        "X": X,
        "Y": Y,
        "L_total": L_total,
        "grid_res": grid_res,
        "x_coords": x_coords,
        "y_coords": y_coords,
        "sources": active_sources,
        "city": city,
        "source_levels": source_levels
    }


def evaluate_single_receiver(
    rx: float,
    ry: float,
    rz: float,
    city: CityLayout,
    sources: List[NoiseSource],
    ground_type: str = "mixed",
    temp_c: float = 20.0,
    rel_humidity: float = 50.0,
    green_buffer: bool = False
) -> Dict[str, Any]:
    """
    Calculates detailed physical attenuation breakdown for a specific probe point (rx, ry, rz).
    Returns per-source terms: A_div, A_atm, A_gr, A_bar, A_misc, and received SPL.
    """
    alpha = calculate_atmospheric_alpha(temp_c, rel_humidity)
    breakdown = []
    total_energy = 10.0 ** (30.0 / 10.0)  # 30 dB ambient floor
    
    # 2D segments for exact line-of-sight intersection check
    segments = build_obstacle_segments(city.buildings, city.barriers)
    
    for s in sources:
        if not s.active:
            continue
        dist_3d = float(np.sqrt((rx - s.x)**2 + (ry - s.y)**2 + (rz - s.z)**2))
        d_eff = max(1.0, dist_3d)
        
        # A_div
        a_div = float(20.0 * np.log10(d_eff) + 11.0)
        
        # A_atm
        a_atm = float(alpha * d_eff / 1000.0)
        
        # A_gr
        a_gr = float(compute_ground_attenuation(np.array([d_eff]), ground_type, s.z, rz)[0])
        
        # Exact ray intersection test with obstacles
        has_obstacle = check_ray_intersection_2d((s.x, s.y), (rx, ry), segments)
        if has_obstacle:
            # Approximate Maekawa barrier diffraction
            delta = 0.25 * (1.0 - np.exp(-d_eff / 40.0))
            n_f = 2.0 * delta / 0.68
            a_bar = float(np.clip(10.0 * np.log10(3.0 + 20.0 * n_f), 6.0, 20.0))
        else:
            a_bar = 0.0
            
        a_misc = float(min(5.0, 0.08 * d_eff)) if green_buffer else 0.0
        
        l_rec = s.lw - (a_div + a_atm + a_gr + a_bar + a_misc)
        total_energy += 10.0 ** (l_rec / 10.0)
        
        breakdown.append({
            "source_name": s.name,
            "source_type": s.stype,
            "distance": round(d_eff, 2),
            "sound_power_lw": round(s.lw, 1),
            "A_div": round(a_div, 2),
            "A_atm": round(a_atm, 2),
            "A_gr": round(a_gr, 2),
            "A_bar": round(a_bar, 2),
            "A_misc": round(a_misc, 2),
            "received_db": round(float(l_rec), 1)
        })
        
    l_tot = 10.0 * np.log10(total_energy)
    return {
        "receiver_coords": (rx, ry, rz),
        "total_db": round(float(l_tot), 1),
        "breakdown": breakdown
    }


def evaluate_facade_exposures(
    city: CityLayout,
    sources: List[NoiseSource],
    ground_type: str = "mixed",
    temp_c: float = 20.0,
    rel_humidity: float = 50.0
) -> List[Dict[str, Any]]:
    """
    Evaluates noise exposure levels at building facades across the city.
    Returns per-building max, average, and compliance status.
    """
    from core.standards import get_cpcb_limit
    
    results = []
    for bld in city.buildings:
        facade_pts = bld.get_facade_points(spacing=15.0)
        if not facade_pts:
            continue
        levels = []
        for fx, fy, fz in facade_pts:
            probe = evaluate_single_receiver(
                fx, fy, fz, city, sources, ground_type, temp_c, rel_humidity
            )
            levels.append(probe["total_db"])
            
        max_db = max(levels) if levels else 40.0
        mean_db = float(np.mean(levels)) if levels else 40.0
        limit = get_cpcb_limit(bld.btype, time_of_day="day")
        compliant = max_db <= limit
        
        results.append({
            "building_id": bld.bid,
            "building_name": bld.name,
            "zone_type": bld.btype,
            "height_m": bld.height,
            "max_facade_db": round(max_db, 1),
            "mean_facade_db": round(mean_db, 1),
            "cpcb_limit_db": limit,
            "exceedance_db": round(max(0.0, max_db - limit), 1),
            "status": "PASS" if compliant else "FAIL"
        })
        
    return results
