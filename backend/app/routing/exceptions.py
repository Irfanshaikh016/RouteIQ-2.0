"""
RouteIQ 2.0 - Routing Subsystem Exceptions (Phase 4)
Defines domain-specific errors for coordinate validation, graph availability,
nearest-node lookups, and pathfinding failures.
"""


class RoutingError(Exception):
    """Base exception for all routing errors."""
    pass


class InvalidCoordinateError(RoutingError):
    """Raised when geographic coordinates are outside valid bounds."""
    pass


class UnsupportedProfileError(RoutingError):
    """Raised when an unrecognized routing profile name is requested."""
    pass


class GraphUnavailableError(RoutingError):
    """Raised when the road network graph has not been loaded or is empty."""
    pass


class NearestNodeNotFoundError(RoutingError):
    """Raised when no road node can be found within the search threshold of coordinates."""
    pass


class NoRouteFoundError(RoutingError):
    """Raised when no valid path exists between origin and destination."""
    pass
