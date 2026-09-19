"""
RouteIQ 2.0 - Route Optimizer & Multi-Profile Comparator (Phase 4)
Computes and compares alternative routes across distinct objective criteria
(Fastest, Safest, Balanced) without ranking or subjective recommendation bias.
"""
from typing import List, Optional
from app.routing.profiles import get_supported_profile_names
from app.routing.route_service import RouteService, get_route_service
from app.routing.schemas import Coordinate, RouteRequest, RouteResponse


class RouteOptimizer:
    """
    Coordinates multi-profile route comparison, computing independent
    trajectories under different objective weight profiles.
    """

    def __init__(self, route_service: Optional[RouteService] = None):
        self.route_service = route_service or get_route_service()

    def compare_routes(
        self,
        origin: Coordinate,
        destination: Coordinate,
        profiles: Optional[List[str]] = None,
        max_nearest_distance_km: float = 50.0,
    ) -> List[RouteResponse]:
        """
        Computes routes across multiple profiles (defaults to fastest, safest, balanced).
        Returns each profile result objectively without subjective winner ranking.
        """
        eval_profiles = profiles or ["fastest", "safest", "balanced"]
        supported = get_supported_profile_names()
        results: List[RouteResponse] = []

        for prof in eval_profiles:
            if prof.strip().lower() in supported:
                req = RouteRequest(
                    origin=origin,
                    destination=destination,
                    profile=prof.strip().lower(),
                    max_nearest_distance_km=max_nearest_distance_km,
                )
                route = self.route_service.calculate_route(req)
                results.append(route)

        return results


# Global singleton instance
_optimizer = RouteOptimizer()


def get_route_optimizer() -> RouteOptimizer:
    """Returns global RouteOptimizer instance."""
    return _optimizer
