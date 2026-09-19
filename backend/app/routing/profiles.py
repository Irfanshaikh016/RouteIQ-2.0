"""
RouteIQ 2.0 - Centralized Routing Profiles (Phase 4)
Defines deterministic multi-criteria objective weights for Fastest, Safest,
and Balanced routing modes.
"""
from typing import Any, Dict, List, Optional, Set
from app.routing.exceptions import UnsupportedProfileError

ROUTING_PROFILES: Dict[str, Dict[str, Any]] = {
    "fastest": {
        "name": "fastest",
        "description": "Optimizes primarily for minimized transit duration along high-speed corridors.",
        "weights": {
            "distance_weight": 0.20,
            "time_weight": 0.60,
            "risk_weight": 0.10,
            "terrain_weight": 0.10,
        },
        "trade_offs": "May select high-elevation mountain segments or rainfall-prone stretches if they offer higher posted speeds.",
    },
    "safest": {
        "name": "safest",
        "description": "Prioritizes hazard avoidance, minimizing exposure to landslides, steep slopes, and flood plains.",
        "weights": {
            "distance_weight": 0.10,
            "time_weight": 0.10,
            "risk_weight": 0.50,
            "terrain_weight": 0.30,
        },
        "trade_offs": "Accepts higher cumulative distance and travel duration in order to detour around vulnerable terrain.",
    },
    "balanced": {
        "name": "balanced",
        "description": "Pragmatic multi-objective equilibrium balancing delivery schedule efficiency with corridor safety.",
        "weights": {
            "distance_weight": 0.25,
            "time_weight": 0.35,
            "risk_weight": 0.25,
            "terrain_weight": 0.15,
        },
        "trade_offs": "Avoids severe hazard bottlenecks while maintaining competitive commercial freight delivery times.",
    },
}


def get_supported_profile_names() -> Set[str]:
    """Returns the set of registered profile names."""
    return set(ROUTING_PROFILES.keys())


def get_profile(name: str) -> Dict[str, Any]:
    """Retrieves profile definition or raises UnsupportedProfileError."""
    normalized = name.strip().lower()
    if normalized not in ROUTING_PROFILES:
        raise UnsupportedProfileError(
            f"Unsupported routing profile '{name}'. Supported profiles: {', '.join(sorted(ROUTING_PROFILES.keys()))}"
        )
    return ROUTING_PROFILES[normalized]


def list_profiles() -> List[Dict[str, Any]]:
    """Returns all available routing profile definitions."""
    return list(ROUTING_PROFILES.values())
