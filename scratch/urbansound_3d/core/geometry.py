"""
Urban Geometry Engine.
Generates synthetic cities, parses OSM building geometries, and manages sound barrier geometries.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from shapely.geometry import Polygon, LineString, Point, box

class Building:
    def __init__(self, bid: str, name: str, polygon: Polygon, height: float, btype: str = "Residential"):
        self.bid = bid
        self.name = name
        self.polygon = polygon
        self.height = height
        self.btype = btype
        minx, miny, maxx, maxy = polygon.bounds
        self.bounds = (minx, miny, maxx, maxy)
        self.centroid = (polygon.centroid.x, polygon.centroid.y)

    def get_facade_points(self, spacing: float = 10.0) -> List[Tuple[float, float, float]]:
        """Sample points along the perimeter at 1.5m receiver height (facade receivers)."""
        points = []
        coords = list(self.polygon.exterior.coords)
        for i in range(len(coords) - 1):
            p1 = np.array(coords[i])
            p2 = np.array(coords[i + 1])
            seg_len = np.linalg.norm(p2 - p1)
            if seg_len < 1e-3:
                continue
            num_pts = max(1, int(np.ceil(seg_len / spacing)))
            for t in np.linspace(0.1, 0.9, num_pts):
                pt = p1 + t * (p2 - p1)
                points.append((float(pt[0]), float(pt[1]), 1.5))
        return points

class SoundBarrier:
    def __init__(self, x1: float, y1: float, x2: float, y2: float, height: float = 4.0, name: str = "Acoustic Wall"):
        self.name = name
        self.line = LineString([(x1, y1), (x2, y2)])
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.height = height

class CityLayout:
    def __init__(self, name: str, width: float = 300.0, height: float = 300.0):
        self.name = name
        self.width = width
        self.height = height
        self.buildings: List[Building] = []
        self.roads: List[Dict[str, Any]] = []
        self.barriers: List[SoundBarrier] = []

    def add_building(self, bid: str, name: str, poly_coords: List[Tuple[float, float]], height: float, btype: str):
        poly = Polygon(poly_coords)
        self.buildings.append(Building(bid, name, poly, height, btype))

    def add_road(self, name: str, start: Tuple[float, float], end: Tuple[float, float], lanes: int = 2, traffic_vol: int = 1200):
        self.roads.append({
            "name": name,
            "start": start,
            "end": end,
            "lanes": lanes,
            "traffic_vol": traffic_vol
        })

    def add_barrier(self, barrier: SoundBarrier):
        self.barriers.append(barrier)

    def clear_barriers(self):
        self.barriers.clear()


def create_residential_colony() -> CityLayout:
    """Creates a 300x300m peaceful residential colony with a school, clinic, villas, and medium apartments."""
    city = CityLayout("Residential Colony", 300.0, 300.0)
    
    # Main transit road at south boundary (y = 25)
    city.add_road("Arterial South Road", (0.0, 25.0), (300.0, 25.0), lanes=4, traffic_vol=1800)
    # Colony internal collector road (x = 150)
    city.add_road("Central Colony Avenue", (150.0, 25.0), (150.0, 280.0), lanes=2, traffic_vol=400)
    
    # South frontage commercial/mixed buildings (shielding colony slightly)
    city.add_building("B_COM1", "Colony Shopping Plaza", [(30, 40), (90, 40), (90, 60), (30, 60)], 14.0, "Commercial Area")
    city.add_building("B_COM2", "Community Clinic & Pharmacy", [(210, 40), (270, 40), (270, 60), (210, 60)], 10.0, "Silence Zone")
    
    # West Sector - Residential Apartments
    city.add_building("B_APT1", "Palm Grove Block A", [(30, 90), (75, 90), (75, 130), (30, 130)], 22.0, "Residential Area")
    city.add_building("B_APT2", "Palm Grove Block B", [(30, 160), (75, 160), (75, 200), (30, 200)], 25.0, "Residential Area")
    city.add_building("B_APT3", "Palm Grove Block C", [(30, 230), (75, 230), (75, 270), (30, 270)], 20.0, "Residential Area")
    
    # Central West - School & Playground
    city.add_building("B_SCH1", "Heritage Primary School", [(95, 170), (135, 170), (135, 230), (95, 230)], 12.0, "Silence Zone")
    
    # East Sector - Residential Villas & Townhomes
    for row, y_pos in enumerate([100, 150, 200, 250]):
        city.add_building(f"B_VIL1_{row}", f"Green Villa {row*2+1}", [(175, y_pos), (215, y_pos), (215, y_pos+30), (175, y_pos+30)], 8.0, "Residential Area")
        city.add_building(f"B_VIL2_{row}", f"Green Villa {row*2+2}", [(235, y_pos), (275, y_pos), (275, y_pos+30), (235, y_pos+30)], 8.0, "Residential Area")
        
    return city


def create_dense_downtown() -> CityLayout:
    """Creates a high-density 300x300m downtown grid with high-rises and crossing avenues."""
    city = CityLayout("Dense Downtown", 300.0, 300.0)
    
    # Main intersecting transit corridors
    city.add_road("Metropolitan Grand Blvd", (0.0, 150.0), (300.0, 150.0), lanes=6, traffic_vol=3200)
    city.add_road("Financial Central Way", (150.0, 0.0), (150.0, 300.0), lanes=4, traffic_vol=2400)
    
    # Quad 1: Southwest Commercial & Corporate Towers
    city.add_building("D_SW1", "Apex FinTech Tower", [(25, 25), (75, 25), (75, 70), (25, 70)], 54.0, "Commercial Area")
    city.add_building("D_SW2", "Metro World Exchange", [(90, 25), (130, 25), (130, 70), (90, 70)], 42.0, "Commercial Area")
    city.add_building("D_SW3", "Silicon Hub Building", [(25, 85), (75, 85), (75, 130), (25, 130)], 48.0, "Commercial Area")
    city.add_building("D_SW4", "South Retail Galleria", [(90, 85), (130, 85), (130, 130), (90, 130)], 26.0, "Commercial Area")
    
    # Quad 2: Southeast Civic & Hospital Center
    city.add_building("D_SE1", "General City Hospital", [(170, 25), (225, 25), (225, 80), (170, 80)], 32.0, "Silence Zone")
    city.add_building("D_SE2", "Hospital Diagnostic Wing", [(240, 25), (280, 25), (280, 80), (240, 80)], 24.0, "Silence Zone")
    city.add_building("D_SE3", "Civic Center & Library", [(170, 95), (225, 95), (225, 135), (170, 135)], 18.0, "Silence Zone")
    city.add_building("D_SE4", "Grand Hotel Metropolis", [(240, 95), (280, 95), (280, 135), (240, 135)], 45.0, "Commercial Area")
    
    # Quad 3: Northwest Mixed Residential Skyscrapers
    city.add_building("D_NW1", "Skyline Heights Tower A", [(25, 170), (75, 170), (75, 220), (25, 220)], 62.0, "Residential Area")
    city.add_building("D_NW2", "Skyline Heights Tower B", [(90, 170), (130, 170), (130, 220), (90, 220)], 58.0, "Residential Area")
    city.add_building("D_NW3", "Urban Loft Condos", [(25, 235), (75, 235), (75, 280), (25, 280)], 36.0, "Residential Area")
    city.add_building("D_NW4", "Metropolitan Arts Academy", [(90, 235), (130, 235), (130, 280), (90, 280)], 20.0, "Silence Zone")
    
    # Quad 4: Northeast Commercial Plaza
    city.add_building("D_NE1", "Innovation Centre Tower", [(170, 170), (225, 170), (225, 220), (170, 220)], 50.0, "Commercial Area")
    city.add_building("D_NE2", "Venture Capital Park", [(240, 170), (280, 170), (280, 220), (240, 220)], 46.0, "Commercial Area")
    city.add_building("D_NE3", "Prestige Residences", [(170, 235), (225, 235), (225, 280), (170, 280)], 38.0, "Residential Area")
    city.add_building("D_NE4", "Pinnacle Executive Suites", [(240, 235), (280, 235), (280, 280), (240, 280)], 40.0, "Residential Area")
    
    return city


def create_industrial_residential_mix() -> CityLayout:
    """Creates a 300x300m mixed zone with heavy industrial facilities, a highway buffer, and a residential enclave."""
    city = CityLayout("Industrial + Residential Mix", 300.0, 300.0)
    
    # Central arterial highway dividing the zones
    city.add_road("Industrial Freight Highway", (0.0, 140.0), (300.0, 140.0), lanes=6, traffic_vol=3600)
    
    # South Half: Heavy Industrial Zone
    city.add_building("IND_1", "Precision Metal Stamping Plant", [(30, 30), (120, 30), (120, 90), (30, 90)], 16.0, "Industrial Area")
    city.add_building("IND_2", "Logistics & Distribution Depot", [(150, 30), (270, 30), (270, 80), (150, 80)], 14.0, "Industrial Area")
    city.add_building("IND_3", "Heavy Fabrication Workshop", [(30, 100), (90, 100), (90, 130), (30, 130)], 12.0, "Industrial Area")
    city.add_building("IND_4", "Chemical Storage Annex", [(180, 95), (240, 95), (240, 130), (180, 130)], 10.0, "Industrial Area")
    
    # North Half: Residential & School Community
    city.add_building("RES_N1", "Riverside Housing Block 1", [(30, 170), (85, 170), (85, 215), (30, 215)], 20.0, "Residential Area")
    city.add_building("RES_N2", "Riverside Housing Block 2", [(105, 170), (160, 170), (160, 215), (105, 215)], 20.0, "Residential Area")
    city.add_building("RES_N3", "Riverside Housing Block 3", [(180, 170), (235, 170), (235, 215), (180, 215)], 20.0, "Residential Area")
    city.add_building("RES_N4", "Suburban Senior Living", [(250, 170), (285, 170), (285, 215), (250, 215)], 15.0, "Residential Area")
    
    # Far North - Quiet community school and kindergarten
    city.add_building("RES_SCH", "Valley View Public School", [(80, 240), (160, 240), (160, 285), (80, 285)], 12.0, "Silence Zone")
    city.add_building("RES_HLTH", "Community Health Centre", [(180, 240), (240, 240), (240, 280), (180, 280)], 10.0, "Silence Zone")
    
    return city


def fetch_osm_city(place_name: str) -> Tuple[Optional[CityLayout], str]:
    """
    Attempts to download real urban geometry using OSMnx if available and network is active.
    Returns (CityLayout, status_message). Cleanly falls back to synthetic if unavailable.
    """
    try:
        import osmnx as ox
        # Try fetching footprints in a 300m box
        gdf = ox.geometries_from_place(place_name, tags={"building": True})
        if gdf.empty:
            return None, f"No building footprints found for '{place_name}'. Using synthetic city fallback."
            
        city = CityLayout(f"OSM: {place_name}", 300.0, 300.0)
        # Normalize geometries to 300x300 bounding box
        total_bounds = gdf.total_bounds # minx, miny, maxx, maxy
        scale_x = 280.0 / max(1.0, (total_bounds[2] - total_bounds[0]))
        scale_y = 280.0 / max(1.0, (total_bounds[3] - total_bounds[1]))
        
        count = 0
        for idx, row in gdf.iterrows():
            geom = row.geometry
            if geom.geom_type == 'Polygon':
                pts = list(geom.exterior.coords)
                norm_pts = [
                    (10.0 + (x - total_bounds[0]) * scale_x, 10.0 + (y - total_bounds[1]) * scale_y)
                    for x, y in pts
                ]
                height = float(row.get('height', 15.0) if 'height' in row and str(row['height']).replace('.','').isdigit() else 18.0)
                city.add_building(f"OSM_{count}", f"Building {count+1}", norm_pts, height, "Residential Area")
                count += 1
                if count >= 30: # Limit count for interactive speed
                    break
                    
        return city, f"Successfully loaded {count} buildings from OpenStreetMap."
    except Exception as e:
        return None, f"OSMnx offline or network unavailable ({type(e).__name__}). Using high-fidelity synthetic city model."
