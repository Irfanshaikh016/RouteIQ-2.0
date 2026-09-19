"""
RouteIQ 2.0 - Dynamic Routing & Graph Immutability Tests (Phase 6)
Tests dynamic edge cost adjustments, road closure avoidance, and graph immutability.
"""
from datetime import datetime, timedelta, timezone
import pytest
from app.repositories.store import get_store
from app.weather.risk import calculate_dynamic_edge_cost, CLOSED_ROAD_IMPEDANCE
from app.weather.schemas import RoadRestrictionStatus


@pytest.fixture
def dynamic_routing_setup():
    store = get_store()
    store.clear()

    u_attrs = {"id": "node-1", "latitude": 26.1445, "longitude": 91.7362, "elevation": 55.0}
    v_attrs = {"id": "node-2", "latitude": 26.1600, "longitude": 91.7500, "elevation": 60.0}
    edge_attrs = {
        "id": "edge-guwahati-bypass",
        "length_meters": 2500.0,
        "maxspeed_kph": 60.0,
        "highway_type": "primary",
        "surface": "asphalt",
        "gradient": 0.02,
        "lanes": 2,
    }
    weights = {
        "distance_weight": 0.25,
        "time_weight": 0.35,
        "risk_weight": 0.25,
        "terrain_weight": 0.15,
    }
    return {
        "store": store,
        "u_attrs": u_attrs,
        "v_attrs": v_attrs,
        "edge_attrs": edge_attrs,
        "weights": weights,
    }


def test_base_dynamic_cost_matches_baseline_when_no_hazards(dynamic_routing_setup):
    s = dynamic_routing_setup
    cost, breakdown, risk, time_sec, is_closed = calculate_dynamic_edge_cost(
        u_attrs=s["u_attrs"],
        v_attrs=s["v_attrs"],
        edge_attrs=s["edge_attrs"],
        weights=s["weights"],
        store=s["store"],
    )
    assert not is_closed
    assert cost > 0.0
    assert cost < 1000.0
    assert time_sec > 0.0
    assert breakdown["dynamic_hazard_cost"] == 0.0


def test_graph_immutability_during_dynamic_evaluation(dynamic_routing_setup):
    s = dynamic_routing_setup
    original_edge_copy = dict(s["edge_attrs"])

    calculate_dynamic_edge_cost(
        u_attrs=s["u_attrs"],
        v_attrs=s["v_attrs"],
        edge_attrs=s["edge_attrs"],
        weights=s["weights"],
        store=s["store"],
    )

    # Ensure edge attributes dictionary was not mutated in-place
    assert s["edge_attrs"] == original_edge_copy


def test_closed_road_restriction_enforces_infinite_impedance(dynamic_routing_setup):
    s = dynamic_routing_setup
    store = s["store"]

    now = datetime.now(timezone.utc)
    # Register CLOSED road restriction on this edge
    store.set_road_restriction(
        road_edge_id="edge-guwahati-bypass",
        status="CLOSED",
        reason="Submerged due to Brahmaputra flood surge",
        speed_multiplier=0.0,
        starts_at=now,
        expires_at=now + timedelta(hours=8),
    )

    cost, breakdown, risk, time_sec, is_closed = calculate_dynamic_edge_cost(
        u_attrs=s["u_attrs"],
        v_attrs=s["v_attrs"],
        edge_attrs=s["edge_attrs"],
        weights=s["weights"],
        store=store,
    )
    assert is_closed is True
    assert cost == CLOSED_ROAD_IMPEDANCE
    assert breakdown["status"] == "CLOSED"


def test_slow_road_restriction_increases_travel_time_and_cost(dynamic_routing_setup):
    s = dynamic_routing_setup
    store = s["store"]

    # Calculate base without restriction
    cost_base, _, _, time_base, _ = calculate_dynamic_edge_cost(
        u_attrs=s["u_attrs"],
        v_attrs=s["v_attrs"],
        edge_attrs=s["edge_attrs"],
        weights=s["weights"],
        store=store,
    )

    now = datetime.now(timezone.utc)
    # Register SLOW road restriction with speed multiplier 0.25 (4x slower)
    store.set_road_restriction(
        road_edge_id="edge-guwahati-bypass",
        status="SLOW",
        reason="Heavy waterlogging - single lane open at crawl speed",
        speed_multiplier=0.25,
        starts_at=now,
        expires_at=now + timedelta(hours=4),
    )

    cost_slow, breakdown_slow, _, time_slow, is_closed = calculate_dynamic_edge_cost(
        u_attrs=s["u_attrs"],
        v_attrs=s["v_attrs"],
        edge_attrs=s["edge_attrs"],
        weights=s["weights"],
        store=store,
    )

    assert is_closed is False
    assert time_slow > time_base
    assert cost_slow > cost_base
