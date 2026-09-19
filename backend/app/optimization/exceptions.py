"""
RouteIQ 2.0 - Fleet Optimization Exceptions (Phase 6)
"""


class OptimizationError(Exception):
    """Base exception for fleet optimization."""
    pass


class InfeasibleOptimizationError(OptimizationError):
    """Raised when OR-Tools cannot find a solution satisfying all constraints."""
    def __init__(self, message: str, reason: str = "INFEASIBLE_CONSTRAINTS", details: dict = None):
        super().__init__(message)
        self.reason = reason
        self.details = details or {}


class InsufficientCapacityError(InfeasibleOptimizationError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, reason="INSUFFICIENT_CAPACITY", details=details)


class InfeasibleTimeWindowError(InfeasibleOptimizationError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, reason="NO_FEASIBLE_TIME_WINDOW", details=details)


class OptimizationEngineError(OptimizationError):
    """Raised when an internal solver or matrix computation error occurs."""
    pass
