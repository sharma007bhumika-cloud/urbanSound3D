"""
Acoustic Noise Source Engine.
Models point sources, acoustic presets, road traffic line sources, and day/night diurnal variations.
"""

from typing import List, Dict, Any, Tuple
import numpy as np

# Standard Sound Power Levels L_w in dB(A) for typical urban noise sources
SOURCE_PRESETS = {
    "Passenger Car (50 km/h)": {
        "lw": 86.0,
        "height": 0.5,
        "category": "Traffic",
        "description": "Standard sedan cruising on dry asphalt"
    },
    "Heavy Commercial Truck": {
        "lw": 98.0,
        "height": 1.2,
        "category": "Traffic",
        "description": "Multi-axle diesel freight truck under moderate load"
    },
    "Motorcycle / Scooter": {
        "lw": 91.0,
        "height": 0.6,
        "category": "Traffic",
        "description": "Two-stroke or four-stroke inner city two-wheeler"
    },
    "City Transit Bus": {
        "lw": 95.0,
        "height": 1.0,
        "category": "Traffic",
        "description": "Standard urban public transit diesel/CNG bus"
    },
    "Construction Excavator / Jackhammer": {
        "lw": 108.0,
        "height": 1.5,
        "category": "Industrial / Construction",
        "description": "Heavy hydraulic breaker or diesel excavator"
    },
    "Public Address Loudspeaker": {
        "lw": 102.0,
        "height": 3.0,
        "category": "Civic",
        "description": "High-output directional or omni horn speaker"
    },
    "Industrial Cooling Tower / Compressor": {
        "lw": 104.0,
        "height": 2.5,
        "category": "Industrial / Construction",
        "description": "Centrifugal chiller, cooling fan, or compressor"
    }
}

class NoiseSource:
    def __init__(self, sid: str, name: str, x: float, y: float, z: float, lw: float, stype: str = "Custom"):
        self.sid = sid
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.lw = lw  # Sound power level in dB(A)
        self.stype = stype
        self.active = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sid": self.sid,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "lw": self.lw,
            "stype": self.stype,
            "active": self.active
        }

def discretize_road_to_sources(
    road_name: str,
    start: Tuple[float, float],
    end: Tuple[float, float],
    traffic_vol: float = 1200.0,
    heavy_pct: float = 15.0,
    spacing: float = 20.0,
    time_of_day: str = "day"
) -> List[NoiseSource]:
    """
    Discretizes a continuous road traffic stream into discrete point sources along centerline.
    Uses simplified NMPB / FHWA empirical traffic sound emission formulation:
    L_eq emission per meter depends on traffic volume Q (veh/hr) and heavy vehicle fraction.
    """
    # Diurnal scaling: night traffic is typically 15-20% of daytime peak
    q = traffic_vol if "day" in time_of_day.lower() else traffic_vol * 0.20
    q = max(1.0, q)
    
    # Sound power per vehicle pass-by: light vehicle ~86 dB, heavy truck ~98 dB
    f_heavy = np.clip(heavy_pct / 100.0, 0.0, 1.0)
    # Energy mix of single average vehicle
    energy_single = (1.0 - f_heavy) * (10 ** (86.0 / 10.0)) + f_heavy * (10 ** (98.0 / 10.0))
    lw_single = 10.0 * np.log10(energy_single)
    
    # Road line length
    p1 = np.array(start)
    p2 = np.array(end)
    road_len = np.linalg.norm(p2 - p1)
    if road_len < 1e-2:
        return []
        
    num_segments = max(1, int(np.round(road_len / spacing)))
    t_vals = np.linspace(0.5 / num_segments, 1.0 - 0.5 / num_segments, num_segments)
    
    # Each point source represents a segment of length delta_L:
    # Lw_segment = Lw_single + 10*log10(Q / 3600 * (delta_L / speed_in_m_s))
    # Assuming average city speed 40 km/h (11.1 m/s):
    delta_l = road_len / num_segments
    v_mps = 11.11  # 40 km/h
    # Expected number of vehicles on this segment at any instant = (Q / 3600) * (delta_l / v_mps)
    inst_vehicles = (q / 3600.0) * (delta_l / v_mps)
    inst_vehicles = max(1e-4, inst_vehicles)
    
    # Sound power of point source representing this segment
    lw_seg = lw_single + 10.0 * np.log10(inst_vehicles)
    
    sources = []
    for i, t in enumerate(t_vals):
        pos = p1 + t * (p2 - p1)
        sources.append(NoiseSource(
            sid=f"ROAD_{road_name[:4]}_{i}",
            name=f"{road_name} (Seg {i+1})",
            x=float(pos[0]),
            y=float(pos[1]),
            z=0.75,
            lw=round(float(lw_seg), 1),
            stype="Road Traffic"
        ))
    return sources

def get_diurnal_traffic_factors() -> np.ndarray:
    """Returns normalized 24-hour diurnal profile of typical urban traffic (0 to 23 hours)."""
    hours = np.arange(24)
    # Double hump curve: morning rush hour (8-9 AM) and evening rush hour (17-19 PM)
    profile = (
        0.15 + 
        0.85 * (np.exp(-((hours - 8.5) ** 2) / (2 * 1.8 ** 2)) + 
                np.exp(-((hours - 18.0) ** 2) / (2 * 2.2 ** 2))) +
        0.40 * (np.exp(-((hours - 13.5) ** 2) / (2 * 3.0 ** 2)))
    )
    # Normalize peak to 1.0
    return profile / np.max(profile)
