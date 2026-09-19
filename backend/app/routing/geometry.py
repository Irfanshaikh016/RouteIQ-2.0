"""
RouteIQ 2.0 - Route Geometry Generation (Phase 4)
Generates GeoJSON LineString geometries with [longitude, latitude] coordinate formatting.
"""
from typing import Any, Dict, List


def build_geojson_linestring(coordinates: List[List[float]]) -> Dict[str, Any]:
    """
    Constructs a standard GeoJSON LineString object.
    Input: List of [longitude, latitude] coordinate pairs.
    """
    return {
        "type": "LineString",
        "coordinates": coordinates,
    }


def extract_route_coordinates(nodes: List[Dict[str, Any]]) -> List[List[float]]:
    """
    Extracts [longitude, latitude] pairs from an ordered sequence of node entities.
    """
    return [
        [round(float(node["longitude"]), 6), round(float(node["latitude"]), 6)]
        for node in nodes
    ]
