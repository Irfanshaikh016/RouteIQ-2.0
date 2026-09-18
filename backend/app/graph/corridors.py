"""
RouteIQ 2.0 - North Eastern Region (NER) Strategic Road Corridors (Phase 3)
Defines primary highway lifelines across Assam, Meghalaya, Nagaland, Manipur,
Mizoram, Tripura, Arunachal Pradesh, and Sikkim.
"""
from typing import Any, Dict, List, Optional

NER_CORRIDORS: Dict[str, Dict[str, Any]] = {
    "guwahati-shillong-silchar": {
        "id": "guwahati-shillong-silchar",
        "name": "Guwahati - Shillong - Silchar Corridor",
        "national_highway": "NH-06",
        "states_covered": ["Assam", "Meghalaya"],
        "start_point": "Guwahati, Assam",
        "end_point": "Silchar, Assam",
        "approximate_length_km": 320.0,
        "terrain_type": "Hilly / Mountainous Plateau / River Valley",
        "strategic_notes": "Vital economic lifeline connecting Brahmaputra Valley to Barak Valley through Meghalaya plateau. Subject to severe monsoon landslides between Shillong and Jowai.",
        "intermediate_waypoints": [
            {"name": "Guwahati (Khanapara)", "latitude": 26.1158, "longitude": 91.8210, "state": "Assam", "elevation_m": 55.0},
            {"name": "Nongpoh", "latitude": 25.9016, "longitude": 91.8797, "state": "Meghalaya", "elevation_m": 485.0},
            {"name": "Umiam Lake", "latitude": 25.6660, "longitude": 91.9056, "state": "Meghalaya", "elevation_m": 990.0},
            {"name": "Shillong", "latitude": 25.5788, "longitude": 91.8933, "state": "Meghalaya", "elevation_m": 1525.0},
            {"name": "Jowai", "latitude": 25.4496, "longitude": 92.2038, "state": "Meghalaya", "elevation_m": 1380.0},
            {"name": "Khliehriat", "latitude": 25.3524, "longitude": 92.3683, "state": "Meghalaya", "elevation_m": 1200.0},
            {"name": "Silchar", "latitude": 24.8333, "longitude": 92.7789, "state": "Assam", "elevation_m": 25.0},
        ],
    },
    "siliguri-guwahati": {
        "id": "siliguri-guwahati",
        "name": "Siliguri - Guwahati East-West Highway Gateway",
        "national_highway": "NH-27",
        "states_covered": ["West Bengal", "Assam"],
        "start_point": "Siliguri, West Bengal",
        "end_point": "Guwahati, Assam",
        "approximate_length_km": 475.0,
        "terrain_type": "Sub-Himalayan Plains / Brahmaputra Floodplain",
        "strategic_notes": "Primary multi-lane arterial gateway connecting peninsular India via the Siliguri Corridor ('Chicken's Neck') into Northeast India. High freight volume.",
        "intermediate_waypoints": [
            {"name": "Siliguri", "latitude": 26.7271, "longitude": 88.3953, "state": "West Bengal", "elevation_m": 122.0},
            {"name": "Jalpaiguri", "latitude": 26.5405, "longitude": 88.7194, "state": "West Bengal", "elevation_m": 85.0},
            {"name": "Alipurduar", "latitude": 26.4919, "longitude": 89.5271, "state": "West Bengal", "elevation_m": 93.0},
            {"name": "Bongaigaon", "latitude": 26.4800, "longitude": 90.5600, "state": "Assam", "elevation_m": 62.0},
            {"name": "Nalbari", "latitude": 26.4447, "longitude": 91.4398, "state": "Assam", "elevation_m": 49.0},
            {"name": "Guwahati (Jalukbari)", "latitude": 26.1528, "longitude": 91.6625, "state": "Assam", "elevation_m": 54.0},
        ],
    },
    "dimapur-kohima-imphal": {
        "id": "dimapur-kohima-imphal",
        "name": "Dimapur - Kohima - Imphal Mountain Corridor",
        "national_highway": "NH-29 / NH-02",
        "states_covered": ["Nagaland", "Manipur"],
        "start_point": "Dimapur, Nagaland",
        "end_point": "Imphal, Manipur",
        "approximate_length_km": 215.0,
        "terrain_type": "Rugged Mountainous",
        "strategic_notes": "Sole arterial road lifeline connecting Manipur to the national railway railhead at Dimapur. Severe monsoon mudslide vulnerability along Zubza and Pagla Pahar.",
        "intermediate_waypoints": [
            {"name": "Dimapur", "latitude": 25.9068, "longitude": 93.7274, "state": "Nagaland", "elevation_m": 145.0},
            {"name": "Chumukedima", "latitude": 25.7942, "longitude": 93.7744, "state": "Nagaland", "elevation_m": 220.0},
            {"name": "Kohima", "latitude": 25.6751, "longitude": 94.1086, "state": "Nagaland", "elevation_m": 1444.0},
            {"name": "Mao Gate", "latitude": 25.5100, "longitude": 94.1300, "state": "Manipur", "elevation_m": 1780.0},
            {"name": "Senapati", "latitude": 25.2689, "longitude": 94.0198, "state": "Manipur", "elevation_m": 1050.0},
            {"name": "Kangpokpi", "latitude": 25.1480, "longitude": 93.9740, "state": "Manipur", "elevation_m": 990.0},
            {"name": "Imphal", "latitude": 24.8170, "longitude": 93.9368, "state": "Manipur", "elevation_m": 786.0},
        ],
    },
    "shillong-agartala": {
        "id": "shillong-agartala",
        "name": "Shillong - Agartala Southern Highway",
        "national_highway": "NH-08",
        "states_covered": ["Meghalaya", "Assam", "Tripura"],
        "start_point": "Shillong, Meghalaya",
        "end_point": "Agartala, Tripura",
        "approximate_length_km": 460.0,
        "terrain_type": "Hilly Ridge / Valleys / Border Plains",
        "strategic_notes": "Lifeline connecting Tripura to the rest of India via southern Meghalaya and Barak Valley border pass.",
        "intermediate_waypoints": [
            {"name": "Shillong", "latitude": 25.5788, "longitude": 91.8933, "state": "Meghalaya", "elevation_m": 1525.0},
            {"name": "Badarpur", "latitude": 24.9000, "longitude": 92.6000, "state": "Assam", "elevation_m": 20.0},
            {"name": "Karimganj", "latitude": 24.8667, "longitude": 92.3500, "state": "Assam", "elevation_m": 15.0},
            {"name": "Dharmanagar", "latitude": 24.3833, "longitude": 92.1667, "state": "Tripura", "elevation_m": 35.0},
            {"name": "Ambassa", "latitude": 23.9242, "longitude": 91.8486, "state": "Tripura", "elevation_m": 65.0},
            {"name": "Agartala", "latitude": 23.8315, "longitude": 91.2868, "state": "Tripura", "elevation_m": 16.0},
        ],
    },
    "silchar-aizawl": {
        "id": "silchar-aizawl",
        "name": "Silchar - Aizawl Ridge Corridor",
        "national_highway": "NH-306",
        "states_covered": ["Assam", "Mizoram"],
        "start_point": "Silchar, Assam",
        "end_point": "Aizawl, Mizoram",
        "approximate_length_km": 178.0,
        "terrain_type": "Steep Hill Ranges / Escarpments",
        "strategic_notes": "Sole designated national highway carrying essential supplies into Mizoram capital. Highly susceptible to sinking zones and landslides.",
        "intermediate_waypoints": [
            {"name": "Silchar", "latitude": 24.8333, "longitude": 92.7789, "state": "Assam", "elevation_m": 25.0},
            {"name": "Vairengte", "latitude": 24.5122, "longitude": 92.7667, "state": "Mizoram", "elevation_m": 240.0},
            {"name": "Kolasib", "latitude": 24.2250, "longitude": 92.6780, "state": "Mizoram", "elevation_m": 880.0},
            {"name": "Sairang", "latitude": 23.8050, "longitude": 92.6620, "state": "Mizoram", "elevation_m": 210.0},
            {"name": "Aizawl", "latitude": 23.7271, "longitude": 92.7176, "state": "Mizoram", "elevation_m": 1132.0},
        ],
    },
    "guwahati-itanagar": {
        "id": "guwahati-itanagar",
        "name": "Guwahati - Tezpur - Itanagar Foothill Arterial",
        "national_highway": "NH-15 / NH-415",
        "states_covered": ["Assam", "Arunachal Pradesh"],
        "start_point": "Guwahati, Assam",
        "end_point": "Itanagar, Arunachal Pradesh",
        "approximate_length_km": 330.0,
        "terrain_type": "Brahmaputra North Bank Plains / Himalayan Foothills",
        "strategic_notes": "Main connection linking Guwahati with Tezpur and entering the Papum Pare foothills to capital Itanagar and Naharlagun.",
        "intermediate_waypoints": [
            {"name": "Guwahati", "latitude": 26.1445, "longitude": 91.7362, "state": "Assam", "elevation_m": 55.0},
            {"name": "Mangaldai", "latitude": 26.4350, "longitude": 92.0350, "state": "Assam", "elevation_m": 58.0},
            {"name": "Tezpur", "latitude": 26.6338, "longitude": 92.7926, "state": "Assam", "elevation_m": 68.0},
            {"name": "Banderdewa", "latitude": 27.1000, "longitude": 93.8167, "state": "Arunachal Pradesh", "elevation_m": 140.0},
            {"name": "Naharlagun", "latitude": 27.1050, "longitude": 93.6930, "state": "Arunachal Pradesh", "elevation_m": 290.0},
            {"name": "Itanagar", "latitude": 27.0844, "longitude": 93.6053, "state": "Arunachal Pradesh", "elevation_m": 750.0},
        ],
    },
    "siliguri-gangtok": {
        "id": "siliguri-gangtok",
        "name": "Siliguri - Sevoke - Gangtok Teesta Gorge Corridor",
        "national_highway": "NH-10",
        "states_covered": ["West Bengal", "Sikkim"],
        "start_point": "Siliguri, West Bengal",
        "end_point": "Gangtok, Sikkim",
        "approximate_length_km": 114.0,
        "terrain_type": "Deep River Canyon / High Himalayan Elevation",
        "strategic_notes": "Border road running along the volatile Teesta River valley. Chronic monsoon flooding and rockfall bottlenecks at 29th Mile and Rangpo.",
        "intermediate_waypoints": [
            {"name": "Siliguri", "latitude": 26.7271, "longitude": 88.3953, "state": "West Bengal", "elevation_m": 122.0},
            {"name": "Sevoke (Coronation Bridge)", "latitude": 26.8833, "longitude": 88.4667, "state": "West Bengal", "elevation_m": 185.0},
            {"name": "Kalijhora", "latitude": 26.9312, "longitude": 88.4520, "state": "West Bengal", "elevation_m": 220.0},
            {"name": "Melli", "latitude": 27.0911, "longitude": 88.4556, "state": "West Bengal", "elevation_m": 280.0},
            {"name": "Rangpo", "latitude": 27.1764, "longitude": 88.5283, "state": "Sikkim", "elevation_m": 330.0},
            {"name": "Singtam", "latitude": 27.2340, "longitude": 88.4975, "state": "Sikkim", "elevation_m": 420.0},
            {"name": "Gangtok", "latitude": 27.3389, "longitude": 88.6065, "state": "Sikkim", "elevation_m": 1650.0},
        ],
    },
}


def get_corridor(corridor_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a specific corridor definition by ID."""
    return NER_CORRIDORS.get(corridor_id)


def list_corridors() -> List[Dict[str, Any]]:
    """Returns all registered NER corridors."""
    return list(NER_CORRIDORS.values())
