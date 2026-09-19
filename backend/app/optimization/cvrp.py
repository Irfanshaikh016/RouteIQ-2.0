"""
RouteIQ 2.0 - Capacitated Vehicle Routing Problem (CVRP) Solver (Phase 6)
Implements fleet vehicle routing with payload capacity constraints using Google OR-Tools.
"""
from typing import Any, Dict, List, Optional
import uuid
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from app.optimization.constraints import add_capacity_constraints
from app.optimization.exceptions import InfeasibleOptimizationError
from app.optimization.infeasibility import diagnose_infeasibility
from app.optimization.matrix import build_travel_matrices
from app.optimization.schemas import (
    DeliveryItem,
    OptimizationRequest,
    OptimizationResponse,
    OptimizationStop,
    OptimizationVehicleRoute,
    UnservedDeliveryDetail,
    VehicleItem,
)


def solve_cvrp(req: OptimizationRequest, org_id: str) -> OptimizationResponse:
    """
    Solves Capacitated Vehicle Routing Problem (CVRP):
    - Assigns multiple customer delivery stops to available fleet vehicles
    - Enforces that no vehicle exceeds its rated payload capacity
    - Starts and ends each vehicle route at the central depot
    - Minimizes total multi-objective travel cost based on active profile
    """
    num_deliveries = len(req.deliveries)
    num_vehicles = len(req.vehicles)
    num_nodes = num_deliveries + 1  # 0 is depot, 1..N are deliveries

    # 1. Pre-validation of aggregate capacities
    total_capacity = sum(v.capacity for v in req.vehicles)
    total_demand = sum(d.demand for d in req.deliveries)
    max_vehicle_capacity = max(v.capacity for v in req.vehicles)

    if any(d.demand > max_vehicle_capacity for d in req.deliveries) or total_demand > total_capacity:
        diag = diagnose_infeasibility(req.vehicles, req.deliveries)
        raise InfeasibleOptimizationError(
            message=f"CVRP is infeasible: {diag['reason']}",
            reason=diag["reason"],
            details=diag["details"],
        )

    # 2. Build travel cost & duration matrices
    delivery_coords = [(d.latitude, d.longitude) for d in req.deliveries]
    matrices = build_travel_matrices(
        depot_lat=req.depot_lat,
        depot_lon=req.depot_lon,
        locations=delivery_coords,
        profile_name=req.profile,
    )
    cost_matrix = matrices["cost_matrix"]
    duration_matrix = matrices["duration_matrix"]
    distance_matrix = matrices["distance_matrix"]
    risk_matrix = matrices["risk_matrix"]
    raw_cost_matrix = matrices["raw_cost_matrix"]

    # 3. Initialize OR-Tools Routing Index Manager & Model
    manager = pywrapcp.RoutingIndexManager(num_nodes, num_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)

    # Register distance/cost transit callback
    def cost_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return cost_matrix[from_node][to_node]

    cost_callback_index = routing.RegisterTransitCallback(cost_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(cost_callback_index)

    # 4. Add Capacity Constraints
    demands = [0] + [int(d.demand) for d in req.deliveries]
    vehicle_capacities = [int(v.capacity) for v in req.vehicles]
    capacity_dim_name = add_capacity_constraints(routing, manager, demands, vehicle_capacities)
    capacity_dimension = routing.GetDimensionOrDie(capacity_dim_name)

    # 5. Configure Solver Search Parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 3

    # 6. Solve Problem
    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        diag = diagnose_infeasibility(req.vehicles, req.deliveries, duration_matrix)
        raise InfeasibleOptimizationError(
            message=f"CVRP solver could not find a feasible solution: {diag['reason']}",
            reason=diag["reason"],
            details=diag["details"],
        )

    # 7. Reconstruct Routes & Stops
    routes: List[OptimizationVehicleRoute] = []
    total_system_distance_km = 0.0
    total_system_duration_min = 0.0
    total_system_cost = 0.0
    total_system_risk = 0.0
    vehicles_used = 0
    served_delivery_ids = set()

    for vehicle_idx in range(num_vehicles):
        vehicle = req.vehicles[vehicle_idx]
        index = routing.Start(vehicle_idx)
        stops: List[OptimizationStop] = []
        route_dist_km = 0.0
        route_dur_min = 0.0
        route_cost = 0.0
        route_risk = 0.0
        seq = 1

        # Starting Depot stop
        stops.append(
            OptimizationStop(
                sequence=seq,
                is_depot=True,
                delivery_id=None,
                location_name="Depot / Origin Hub",
                latitude=req.depot_lat,
                longitude=req.depot_lon,
                arrival_time_minutes=0.0,
                departure_time_minutes=0.0,
                load_after_stop=0.0,
                status="departed",
            )
        )

        prev_node = 0
        current_time = 0.0
        route_demand = 0.0

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            if node_index != 0:
                # Customer delivery stop
                deliv_item = req.deliveries[node_index - 1]
                served_delivery_ids.add(deliv_item.delivery_id)
                route_demand += deliv_item.demand

                leg_dur = duration_matrix[prev_node][node_index]
                arrival = current_time + leg_dur
                departure = arrival + deliv_item.service_duration_minutes
                current_time = departure

                route_dist_km += distance_matrix[prev_node][node_index]
                route_dur_min += leg_dur + deliv_item.service_duration_minutes
                route_cost += raw_cost_matrix[prev_node][node_index]
                route_risk += risk_matrix[prev_node][node_index]

                seq += 1
                stops.append(
                    OptimizationStop(
                        sequence=seq,
                        is_depot=False,
                        delivery_id=deliv_item.delivery_id,
                        location_name=f"Stop #{seq - 1}",
                        latitude=deliv_item.latitude,
                        longitude=deliv_item.longitude,
                        arrival_time_minutes=round(arrival, 1),
                        departure_time_minutes=round(departure, 1),
                        load_after_stop=float(route_demand),
                        status="on_time",
                    )
                )
                prev_node = node_index

            index = solution.Value(routing.NextVar(index))

        # Return to depot
        if len(stops) > 1:
            vehicles_used += 1
            leg_dur = duration_matrix[prev_node][0]
            route_dist_km += distance_matrix[prev_node][0]
            route_dur_min += leg_dur
            route_cost += raw_cost_matrix[prev_node][0]
            route_risk += risk_matrix[prev_node][0]

            seq += 1
            stops.append(
                OptimizationStop(
                    sequence=seq,
                    is_depot=True,
                    delivery_id=None,
                    location_name="Depot / Return",
                    latitude=req.depot_lat,
                    longitude=req.depot_lon,
                    arrival_time_minutes=round(current_time + leg_dur, 1),
                    departure_time_minutes=round(current_time + leg_dur, 1),
                    load_after_stop=0.0,
                    status="completed",
                )
            )

            peak_load = round(route_demand, 2)
            utilization_pct = round((peak_load / vehicle.capacity) * 100.0, 1) if vehicle.capacity > 0 else 0.0

            total_system_distance_km += route_dist_km
            total_system_duration_min += route_dur_min
            total_system_cost += route_cost
            total_system_risk += route_risk

            # Generate GeoJSON geometry
            coords = [[s.longitude, s.latitude] for s in stops]
            geometry = {"type": "LineString", "coordinates": coords}

            routes.append(
                OptimizationVehicleRoute(
                    vehicle_id=vehicle.vehicle_id,
                    vehicle_name=vehicle.vehicle_name or f"Vehicle {vehicle_idx + 1}",
                    total_distance_km=round(route_dist_km, 2),
                    total_duration_minutes=round(route_dur_min, 1),
                    total_cost=round(route_cost, 2),
                    total_risk=round(route_risk, 2),
                    capacity=vehicle.capacity,
                    peak_load=peak_load,
                    capacity_utilization_pct=utilization_pct,
                    stops=stops,
                    geometry=geometry,
                )
            )

    # 8. Unserved Deliveries
    unserved: List[UnservedDeliveryDetail] = []
    for d in req.deliveries:
        if d.delivery_id not in served_delivery_ids:
            unserved.append(
                UnservedDeliveryDetail(
                    delivery_id=d.delivery_id,
                    reason="Excluded due to vehicle capacity limits",
                    constraint="vehicle_capacity",
                )
            )

    optimization_id = str(uuid.uuid4())
    return OptimizationResponse(
        optimization_id=optimization_id,
        problem_type="CVRP",
        profile=req.profile,
        status="OPTIMAL" if not unserved else "PARTIAL",
        vehicles_used=vehicles_used,
        total_distance_km=round(total_system_distance_km, 2),
        total_duration_minutes=round(total_system_duration_min, 1),
        total_cost=round(total_system_cost, 2),
        total_risk=round(total_system_risk, 2),
        total_deliveries=num_deliveries,
        served_deliveries_count=len(served_delivery_ids),
        unserved_deliveries=unserved,
        routes=routes,
    )
