"""
RouteIQ 2.0 - Road Network Seeder (Phase 3 & 4)
Seeds baseline NER highway corridors if the road network graph is empty.
"""
import logging
import os
from typing import Optional
from app.graph.corridors import NER_CORRIDORS
from app.graph.network_builder import get_graph_manager
from app.graph.osm_ingestion import OSMIngestionPipeline, haversine_distance
from app.repositories.store import DataStore, get_store

logger = logging.getLogger("routeiq.seeder")


def seed_road_network_if_empty(store: Optional[DataStore] = None) -> int:
    """
    Checks if the road network is empty. If so, seeds the baseline NER road network
    from sample_ner_osm.xml (if available) and all 7 strategic highway corridors.
    Returns the total number of road nodes present.
    """
    target_store = store or get_store()
    current_nodes = len(target_store.road_nodes)
    if current_nodes > 0:
        logger.info(f"Road network already populated with {current_nodes} nodes.")
        return current_nodes

    logger.info("Road network graph is empty. Seeding baseline NER corridor network...")

    # 1. Attempt ingestion of sample OSM fixture if file exists
    fixture_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "tests", "fixtures", "sample_ner_osm.xml"),
        os.path.join(os.getcwd(), "tests", "fixtures", "sample_ner_osm.xml"),
        os.path.join(os.getcwd(), "backend", "tests", "fixtures", "sample_ner_osm.xml"),
    ]
    for fp in fixture_paths:
        if os.path.exists(fp):
            try:
                pipeline = OSMIngestionPipeline(store=target_store)
                pipeline.ingest_file(fp)
                logger.info(f"Successfully ingested OSM fixture from {fp}")
                break
            except Exception as e:
                logger.warning(f"Could not ingest OSM fixture {fp}: {e}")

    # 2. Seed all 7 strategic NER corridors from NER_CORRIDORS
    node_coord_map = {}
    for nid, n in target_store.road_nodes.items():
        key = (round(float(n["latitude"]), 4), round(float(n["longitude"]), 4))
        node_coord_map[key] = nid

    for corridor_id, corridor in NER_CORRIDORS.items():
        waypoints = corridor.get("intermediate_waypoints", [])
        if len(waypoints) < 2:
            continue

        previous_node_id = None
        for wp in waypoints:
            lat = float(wp["latitude"])
            lon = float(wp["longitude"])
            coord_key = (round(lat, 4), round(lon, 4))

            if coord_key in node_coord_map:
                node_id = node_coord_map[coord_key]
            else:
                new_node = target_store.create_road_node(
                    latitude=lat,
                    longitude=lon,
                    elevation_m=wp.get("elevation_m"),
                    metadata={
                        "name": wp.get("name"),
                        "state": wp.get("state"),
                        "corridor": corridor_id,
                    },
                )
                node_id = new_node["id"]
                node_coord_map[coord_key] = node_id

            if previous_node_id and previous_node_id != node_id:
                prev_node = target_store.get_road_node(previous_node_id)
                if prev_node:
                    dist_m = haversine_distance(
                        float(prev_node["latitude"]),
                        float(prev_node["longitude"]),
                        lat,
                        lon,
                    )
                    road_name = f"{corridor.get('national_highway', 'NH')} ({corridor.get('name')})"
                    # Forward edge
                    target_store.create_road_edge(
                        source_node_id=previous_node_id,
                        target_node_id=node_id,
                        road_type="trunk",
                        length_meters=max(dist_m, 100.0),
                        road_name=road_name,
                        max_speed_kph=60.0,
                        oneway=False,
                        metadata={"corridor": corridor_id},
                    )
                    # Backward edge
                    target_store.create_road_edge(
                        source_node_id=node_id,
                        target_node_id=previous_node_id,
                        road_type="trunk",
                        length_meters=max(dist_m, 100.0),
                        road_name=road_name,
                        max_speed_kph=60.0,
                        oneway=False,
                        metadata={"corridor": corridor_id},
                    )

            previous_node_id = node_id

    # 3. Invalidate graph manager cache so fresh graph is built
    get_graph_manager().invalidate_cache()
    total_nodes = len(target_store.road_nodes)
    total_edges = len(target_store.road_edges)
    logger.info(f"Seeded baseline NER road network: {total_nodes} nodes, {total_edges} edges.")
    return total_nodes
