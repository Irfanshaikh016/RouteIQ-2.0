"""
RouteIQ 2.0 - OpenStreetMap (OSM) Ingestion Pipeline (Phase 3)
Parses XML and JSON Overpass data, filters drivable road classes,
computes geodesic Haversine segment lengths, determines directionality,
and saves entities into the road network store.
"""
import math
import re
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Set, Tuple
from app.repositories.store import DataStore, get_store

# Supported drivable road classes for logistics routing
ACCEPTED_HIGHWAYS: Set[str] = {
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "unclassified",
    "residential",
    "service",
    "motorway_link",
    "trunk_link",
    "primary_link",
    "secondary_link",
    "tertiary_link",
}

EARTH_RADIUS_METERS = 6371000.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two geographic coordinates in meters
    using the pure-Python Haversine formula (no C-extension dependencies).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_METERS * c


def parse_max_speed(speed_str: Optional[str]) -> Optional[float]:
    """Parses speed string like '60', '40 km/h', '30 mph' into km/h float."""
    if not speed_str:
        return None
    match = re.search(r"(\d+(\.\d+)?)", speed_str)
    if not match:
        return None
    val = float(match.group(1))
    if "mph" in speed_str.lower():
        val = val * 1.60934
    return val


class OSMIngestionPipeline:
    """
    Parses OSM XML / JSON data, generates graph nodes and edges with
    geodesic lengths and directionality, and commits to the datastore.
    """

    def __init__(self, store: Optional[DataStore] = None):
        self.store = store or get_store()

    def parse_xml_string(self, xml_content: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parses OSM XML content string into raw nodes and edge definitions."""
        root = ET.fromstring(xml_content)

        # 1. Parse all nodes
        nodes_dict: Dict[int, Dict[str, Any]] = {}
        for node_elem in root.findall("node"):
            osm_id = int(node_elem.attrib["id"])
            lat = float(node_elem.attrib["lat"])
            lon = float(node_elem.attrib["lon"])
            tags: Dict[str, str] = {}
            for tag in node_elem.findall("tag"):
                tags[tag.attrib["k"]] = tag.attrib["v"]

            elevation = None
            if "ele" in tags:
                try:
                    elevation = float(tags["ele"])
                except ValueError:
                    pass

            nodes_dict[osm_id] = {
                "osm_id": osm_id,
                "latitude": lat,
                "longitude": lon,
                "elevation_m": elevation,
                "metadata": tags,
            }

        # 2. Parse ways and generate edges
        referenced_node_ids: Set[int] = set()
        edges_raw: List[Dict[str, Any]] = []

        for way_elem in root.findall("way"):
            osm_way_id = int(way_elem.attrib["id"])
            tags: Dict[str, str] = {}
            for tag in way_elem.findall("tag"):
                tags[tag.attrib["k"]] = tag.attrib["v"]

            highway = tags.get("highway")
            if not highway or highway not in ACCEPTED_HIGHWAYS:
                continue

            nd_refs = [int(nd.attrib["ref"]) for nd in way_elem.findall("nd")]
            if len(nd_refs) < 2:
                continue

            road_name = tags.get("name") or tags.get("ref") or f"Way {osm_way_id}"
            max_speed = parse_max_speed(tags.get("maxspeed"))

            oneway_tag = tags.get("oneway", "").lower()
            is_roundabout = tags.get("junction") == "roundabout"
            is_oneway = is_roundabout or oneway_tag in ("yes", "1", "true")
            is_reverse = oneway_tag == "-1"

            for i in range(len(nd_refs) - 1):
                u_osm = nd_refs[i]
                v_osm = nd_refs[i + 1]

                if u_osm not in nodes_dict or v_osm not in nodes_dict:
                    continue

                u_node = nodes_dict[u_osm]
                v_node = nodes_dict[v_osm]

                length_m = haversine_distance(
                    u_node["latitude"], u_node["longitude"],
                    v_node["latitude"], v_node["longitude"]
                )

                referenced_node_ids.add(u_osm)
                referenced_node_ids.add(v_osm)

                if is_reverse:
                    edges_raw.append({
                        "osm_way_id": osm_way_id,
                        "source_osm_id": v_osm,
                        "target_osm_id": u_osm,
                        "road_name": road_name,
                        "road_type": highway,
                        "length_meters": length_m,
                        "max_speed_kph": max_speed,
                        "oneway": True,
                        "metadata": tags,
                    })
                elif is_oneway:
                    edges_raw.append({
                        "osm_way_id": osm_way_id,
                        "source_osm_id": u_osm,
                        "target_osm_id": v_osm,
                        "road_name": road_name,
                        "road_type": highway,
                        "length_meters": length_m,
                        "max_speed_kph": max_speed,
                        "oneway": True,
                        "metadata": tags,
                    })
                else:
                    # Bidirectional road segment
                    edges_raw.append({
                        "osm_way_id": osm_way_id,
                        "source_osm_id": u_osm,
                        "target_osm_id": v_osm,
                        "road_name": road_name,
                        "road_type": highway,
                        "length_meters": length_m,
                        "max_speed_kph": max_speed,
                        "oneway": False,
                        "metadata": tags,
                    })
                    edges_raw.append({
                        "osm_way_id": osm_way_id,
                        "source_osm_id": v_osm,
                        "target_osm_id": u_osm,
                        "road_name": road_name,
                        "road_type": highway,
                        "length_meters": length_m,
                        "max_speed_kph": max_speed,
                        "oneway": False,
                        "metadata": tags,
                    })

        # Only retain nodes that are part of drivable ways
        filtered_nodes = [nodes_dict[nid] for nid in referenced_node_ids]
        return filtered_nodes, edges_raw

    def ingest_xml_string(self, xml_content: str) -> Dict[str, Any]:
        """Parses and commits XML content into the store."""
        start_time = time.time()
        raw_nodes, raw_edges = self.parse_xml_string(xml_content)

        # Ingest nodes first to get database UUIDs
        osm_to_uuid: Dict[int, str] = {}
        nodes_to_insert = []
        for n in raw_nodes:
            existing = self.store.get_road_node_by_osm_id(n["osm_id"])
            if existing:
                osm_to_uuid[n["osm_id"]] = existing["id"]
            else:
                created = self.store.create_road_node(
                    osm_id=n["osm_id"],
                    latitude=n["latitude"],
                    longitude=n["longitude"],
                    elevation_m=n["elevation_m"],
                    metadata=n["metadata"],
                )
                osm_to_uuid[n["osm_id"]] = created["id"]
                nodes_to_insert.append(created)

        # Ingest edges referencing node UUIDs
        edges_to_insert = []
        total_length_m = 0.0
        for e in raw_edges:
            src_uuid = osm_to_uuid.get(e["source_osm_id"])
            tgt_uuid = osm_to_uuid.get(e["target_osm_id"])
            if not src_uuid or not tgt_uuid:
                continue

            edge = self.store.create_road_edge(
                osm_way_id=e["osm_way_id"],
                source_node_id=src_uuid,
                target_node_id=tgt_uuid,
                road_name=e["road_name"],
                road_type=e["road_type"],
                length_meters=e["length_meters"],
                max_speed_kph=e["max_speed_kph"],
                oneway=e["oneway"],
                metadata=e["metadata"],
            )
            edges_to_insert.append(edge)
            total_length_m += e["length_meters"]

        elapsed = time.time() - start_time
        return {
            "success": True,
            "nodes_ingested": len(raw_nodes),
            "edges_ingested": len(edges_to_insert),
            "total_length_km": round(total_length_m / 1000.0, 2),
            "time_taken_seconds": round(elapsed, 4),
            "message": f"Successfully ingested {len(raw_nodes)} nodes and {len(edges_to_insert)} road segments.",
        }

    def ingest_file(self, file_path: str) -> Dict[str, Any]:
        """Ingests OSM XML directly from a local file path."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.ingest_xml_string(content)
