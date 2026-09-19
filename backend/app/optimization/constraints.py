"""
RouteIQ 2.0 - OR-Tools Routing Constraint Builders (Phase 6)
Configures Capacity (CVRP) and Time Window (VRP-TW) dimensions for RoutingModel.
"""
from typing import Callable, List, Tuple
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def add_capacity_constraints(
    routing: pywrapcp.RoutingModel,
    manager: pywrapcp.RoutingIndexManager,
    demands: List[int],
    vehicle_capacities: List[int],
) -> str:
    """
    Adds cumulative vehicle capacity dimension.
    Prevents any vehicle from carrying more payload than its rated capacity.
    """
    def demand_callback(from_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    dimension_name = "Capacity"

    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        vehicle_capacities,  # vehicle maximum capacities
        True,  # start cumul to zero
        dimension_name,
    )
    return dimension_name


def add_time_window_constraints(
    routing: pywrapcp.RoutingModel,
    manager: pywrapcp.RoutingIndexManager,
    duration_matrix: List[List[int]],
    service_durations: List[int],
    time_windows: List[Tuple[int, int]],
    max_time_horizon: int = 1440,  # 24 hours in minutes
) -> pywrapcp.RoutingDimension:
    """
    Adds cumulative time dimension for VRP-TW.
    Enforces that arrival at each stop satisfies [start, end] window.
    """
    def time_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        travel_time = duration_matrix[from_node][to_node]
        service_time = service_durations[from_node]
        return travel_time + service_time

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    dimension_name = "Time"

    routing.AddDimension(
        transit_callback_index,
        max_time_horizon,  # allow waiting time
        max_time_horizon,  # maximum vehicle travel time
        False,  # don't force start cumul to zero
        dimension_name,
    )

    time_dimension = routing.GetDimensionOrDie(dimension_name)

    # Add time window constraints for each delivery node
    for node_idx, (start, end) in enumerate(time_windows):
        index = manager.NodeToIndex(node_idx)
        time_dimension.CumulVar(index).SetRange(int(start), int(end))

    # Add time window constraints for depot starts and ends
    num_vehicles = manager.GetNumberOfVehicles()
    for vehicle_id in range(num_vehicles):
        start_index = routing.Start(vehicle_id)
        end_index = routing.End(vehicle_id)
        # Vehicle can depart depot within first 2 hours
        time_dimension.CumulVar(start_index).SetRange(0, 120)
        time_dimension.CumulVar(end_index).SetRange(0, max_time_horizon)

    return time_dimension
