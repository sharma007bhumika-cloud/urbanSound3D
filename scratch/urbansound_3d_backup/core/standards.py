"""
Acoustic Standards and Regulatory Limits.
Includes Central Pollution Control Board (CPCB), India, and World Health Organization (WHO) limits.

NOTE: Regulatory values are based on The Noise Pollution (Regulation and Control) Rules, 2000
under the Environment (Protection) Act, 1986. Verify values against official CPCB publication tables.
"""

from typing import Dict, Tuple

# CPCB India Ambient Noise Standards (Leq in dB(A))
# Day time: 06:00 to 22:00 (6 AM - 10 PM)
# Night time: 22:00 to 06:00 (10 PM - 6 AM)
CPCB_STANDARDS: Dict[str, Dict[str, float]] = {
    "Industrial Area": {
        "day": 75.0,
        "night": 70.0,
        "description": "Factories, mills, heavy industry zones, logistics hubs."
    },
    "Commercial Area": {
        "day": 65.0,
        "night": 55.0,
        "description": "Markets, retail hubs, commercial complexes, offices."
    },
    "Residential Area": {
        "day": 55.0,
        "night": 45.0,
        "description": "Housing societies, residential townships, urban colonies."
    },
    "Silence Zone": {
        "day": 50.0,
        "night": 40.0,
        "description": "Area within 100m around hospitals, educational institutions, courts."
    }
}

# World Health Organization (WHO) Environmental Noise Guidelines (2018)
WHO_GUIDELINES: Dict[str, Dict[str, float]] = {
    "Road Traffic": {
        "Lden": 53.0,
        "Lnight": 45.0,
        "description": "WHO 2018 conditional recommendation to avoid adverse health outcomes."
    },
    "Railway Noise": {
        "Lden": 54.0,
        "Lnight": 44.0,
        "description": "WHO railway guideline limit."
    },
    "Industrial Noise": {
        "Lden": 65.0,
        "Lnight": 50.0,
        "description": "WHO community noise exposure threshold."
    }
}

# Perceived loudness reference scale for intuitive understanding
PERCEIVED_LEVELS = [
    (0, 30, "Whisper / Faint", "#2ecc71"),
    (30, 45, "Quiet Bedroom", "#27ae60"),
    (45, 55, "Normal Living Room", "#f1c40f"),
    (55, 65, "Moderate Conversation", "#e67e22"),
    (65, 75, "Busy Street / Office", "#e74c3c"),
    (75, 85, "Heavy City Traffic", "#c0392b"),
    (85, 100, "Construction / Loud Horn", "#8e44ad"),
    (100, 140, "Jet Takeoff / Threshold of Pain", "#2c3e50")
]

def get_cpcb_limit(zone: str, time_of_day: str = "day") -> float:
    """Retrieve CPCB threshold limit for given zone and time of day."""
    zone_clean = zone if zone in CPCB_STANDARDS else "Residential Area"
    tod_clean = "night" if "night" in time_of_day.lower() else "day"
    return CPCB_STANDARDS[zone_clean][tod_clean]

def get_noise_category(db: float) -> Tuple[str, str]:
    """Return qualitative category label and hex color for a given decibel level."""
    for low, high, label, color in PERCEIVED_LEVELS:
        if low <= db < high:
            return label, color
    if db >= 100:
        return "Severe Hazard", "#e74c3c"
    return "Ultra Quiet", "#2ecc71"
