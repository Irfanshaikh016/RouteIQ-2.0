"""
RouteIQ 2.0 - Hazard and Risk Assessment Model (Phase 4)
Provides deterministic, modular risk scoring across flood, landslide,
monsoon surface degradation, and mountainous terrain vulnerabilities.

NOTE: These values represent configurable heuristic optimization penalties
for route planning in the North Eastern Region. They do NOT represent live
weather observations or real-time sensor telemetries.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

# Configurable surface degradation penalties under wet/monsoonal conditions
MONSOON_SURFACE_PENALTIES: Dict[str, float] = {
    "asphalt": 0.05,
    "paved": 0.08,
    "concrete": 0.06,
    "paving_stones": 0.20,
    "sett": 0.25,
    "cobblestone": 0.35,
    "compacted": 0.45,
    "fine_gravel": 0.40,
    "gravel": 0.55,
    "ground": 0.70,
    "unpaved": 0.75,
    "dirt": 0.85,
    "earth": 0.90,
    "mud": 0.98,
    "sand": 0.80,
    "default_unknown": 0.25,
}

# Inherent infrastructure risk by road classification
ROAD_CLASS_RISK: Dict[str, float] = {
    "motorway": 0.05,
    "trunk": 0.10,
    "primary": 0.15,
    "secondary": 0.25,
    "tertiary": 0.40,
    "unclassified": 0.55,
    "residential": 0.30,
    "service": 0.45,
    "motorway_link": 0.08,
    "trunk_link": 0.12,
    "primary_link": 0.18,
    "secondary_link": 0.28,
    "tertiary_link": 0.42,
}


class HazardProvider(ABC):
    """
    Abstract interface for hazard risk assessment.
    Enables future pluggable replacement with LiveWeatherHazardProvider,
    SatelliteHazardProvider, or MLHazardProvider without altering the pathfinder.
    """

    @abstractmethod
    def calculate_risk(
        self,
        u_attrs: Dict[str, Any],
        v_attrs: Dict[str, Any],
        edge_attrs: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Computes normalized risk components for a directed road segment (u -> v).
        Returns dictionary with keys: flood_risk, landslide_risk, monsoon_risk,
        terrain_risk, surface_risk, overall_risk (all in [0.0, 1.0]).
        """
        pass


class StaticHazardProvider(HazardProvider):
    """
    Deterministic baseline hazard provider using road class heuristics,
    elevation deltas, surface degradation tables, and NER terrain context.
    """

    def calculate_risk(
        self,
        u_attrs: Dict[str, Any],
        v_attrs: Dict[str, Any],
        edge_attrs: Dict[str, Any],
    ) -> Dict[str, float]:
        tags = edge_attrs.get("metadata", {})
        road_type = edge_attrs.get("road_type", "unclassified").lower()

        # 1. Surface degradation risk
        surface = tags.get("surface", "").lower()
        surface_risk = MONSOON_SURFACE_PENALTIES.get(
            surface, MONSOON_SURFACE_PENALTIES["default_unknown"]
        )

        # 2. Terrain & elevation gradient risk
        u_ele = u_attrs.get("elevation_m") or 0.0
        v_ele = v_attrs.get("elevation_m") or 0.0
        ele_diff = abs(v_ele - u_ele)
        length_m = max(float(edge_attrs.get("length_meters", 100.0)), 1.0)
        grade = ele_diff / length_m

        # Normalize grade risk: 0% slope = 0.0, >=12% steep mountain grade = 1.0
        grade_risk = min(grade / 0.12, 1.0)
        # Higher altitude sections (>1000m) in Khasi/Naga/Barail hills have increased landslide exposure
        max_ele = max(u_ele, v_ele)
        altitude_factor = min(max(max_ele - 500.0, 0.0) / 1500.0, 1.0)
        terrain_risk = round(0.6 * grade_risk + 0.4 * altitude_factor, 4)

        # 3. Landslide risk heuristic (steep slopes + unpaved/tertiary roads in high elevations)
        landslide_risk = round(
            min(0.5 * grade_risk + 0.3 * altitude_factor + 0.2 * surface_risk, 1.0),
            4,
        )

        # 4. Flood risk heuristic (low elevation river valley floodplains <= 60m like Brahmaputra basin)
        if max_ele <= 65.0:
            flood_risk = 0.60 if road_type in ("secondary", "tertiary", "unclassified") else 0.30
        elif max_ele <= 120.0:
            flood_risk = 0.20
        else:
            flood_risk = 0.05

        # 5. Monsoon risk heuristic (combination of surface vulnerability + flood/landslide exposure)
        class_base = ROAD_CLASS_RISK.get(road_type, 0.35)
        monsoon_risk = round(
            min(0.4 * surface_risk + 0.3 * landslide_risk + 0.2 * flood_risk + 0.1 * class_base, 1.0),
            4,
        )

        # 6. Overall composite risk
        overall_risk = round(
            0.25 * flood_risk
            + 0.30 * landslide_risk
            + 0.20 * monsoon_risk
            + 0.15 * terrain_risk
            + 0.10 * surface_risk,
            4,
        )

        return {
            "flood_risk": min(max(flood_risk, 0.0), 1.0),
            "landslide_risk": min(max(landslide_risk, 0.0), 1.0),
            "monsoon_risk": min(max(monsoon_risk, 0.0), 1.0),
            "terrain_risk": min(max(terrain_risk, 0.0), 1.0),
            "surface_risk": min(max(surface_risk, 0.0), 1.0),
            "overall_risk": min(max(overall_risk, 0.0), 1.0),
        }


# Global default hazard provider instance
_default_hazard_provider = StaticHazardProvider()


def get_default_hazard_provider() -> HazardProvider:
    """Returns the configured HazardProvider instance."""
    return _default_hazard_provider
