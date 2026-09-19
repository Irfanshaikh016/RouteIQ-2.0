"""
RouteIQ 2.0 - Fleet Optimization Infeasibility Diagnostic Engine (Phase 6)
Analyzes constraint violations and generates structured diagnostics when a fleet
problem cannot be solved.
"""
from typing import Any, Dict, List, Optional
from app.optimization.schemas import DeliveryItem, VehicleItem


def diagnose_infeasibility(
    vehicles: List[VehicleItem],
    deliveries: List[DeliveryItem],
    duration_matrix: Optional[List[List[int]]] = None,
) -> Dict[str, Any]:
    """
    Analyzes inputs to provide structured explanation instead of generic solver failure.
    Returns:
        {
            "reason": str,
            "constraint": str,
            "unserved_deliveries": List[Dict[str, str]],
            "details": Dict[str, Any]
        }
    """
    # 1. No vehicles available
    if not vehicles:
        return {
            "reason": "NO_AVAILABLE_VEHICLES",
            "constraint": "fleet_availability",
            "unserved_deliveries": [{"delivery_id": d.delivery_id, "reason": "No vehicles in fleet"} for d in deliveries],
            "details": {"message": "At least one vehicle with positive capacity is required."},
        }

    # 2. Total capacity exceeded
    total_capacity = sum(v.capacity for v in vehicles)
    total_demand = sum(d.demand for d in deliveries)
    max_vehicle_capacity = max(v.capacity for v in vehicles)

    oversized = [d for d in deliveries if d.demand > max_vehicle_capacity]
    if oversized:
        return {
            "reason": "DELIVERY_EXCEEDS_MAX_CAPACITY",
            "constraint": "vehicle_capacity",
            "unserved_deliveries": [
                {
                    "delivery_id": d.delivery_id,
                    "reason": f"Delivery demand ({d.demand} kg) exceeds largest vehicle capacity ({max_vehicle_capacity} kg)",
                }
                for d in oversized
            ],
            "details": {
                "max_vehicle_capacity": max_vehicle_capacity,
                "oversized_deliveries_count": len(oversized),
            },
        }

    if total_demand > total_capacity:
        return {
            "reason": "INSUFFICIENT_CAPACITY",
            "constraint": "total_fleet_capacity",
            "unserved_deliveries": [
                {
                    "delivery_id": d.delivery_id,
                    "reason": f"Total demand ({total_demand} kg) exceeds aggregate fleet capacity ({total_capacity} kg)",
                }
                for d in deliveries
            ],
            "details": {
                "total_demand": total_demand,
                "total_capacity": total_capacity,
                "deficit": total_demand - total_capacity,
            },
        }

    # 3. Time window check (for VRPTW)
    if duration_matrix:
        infeasible_windows = []
        for idx, d in enumerate(deliveries):
            node_idx = idx + 1
            if d.time_window_start_minutes is not None and d.time_window_end_minutes is not None:
                if d.time_window_start_minutes > d.time_window_end_minutes:
                    infeasible_windows.append({
                        "delivery_id": d.delivery_id,
                        "reason": f"Start time ({d.time_window_start_minutes}m) is after end time ({d.time_window_end_minutes}m)",
                    })
                else:
                    # Minimum travel time from depot (node 0)
                    min_travel = duration_matrix[0][node_idx]
                    if min_travel > d.time_window_end_minutes:
                        infeasible_windows.append({
                            "delivery_id": d.delivery_id,
                            "reason": f"Earliest arrival from depot ({min_travel}m) exceeds delivery window deadline ({d.time_window_end_minutes}m)",
                        })

        if infeasible_windows:
            return {
                "reason": "NO_FEASIBLE_TIME_WINDOW",
                "constraint": "time_windows",
                "unserved_deliveries": infeasible_windows,
                "details": {
                    "infeasible_windows_count": len(infeasible_windows),
                },
            }

    # 4. Generic infeasible constraint
    return {
        "reason": "INFEASIBLE_CONSTRAINTS",
        "constraint": "combinatorial_conflict",
        "unserved_deliveries": [{"delivery_id": d.delivery_id, "reason": "No feasible route permutation"} for d in deliveries],
        "details": {"message": "Constraints could not be reconciled by solver within time limit."},
    }
