"""
RouteIQ 2.0 API v1 Router Aggregator.
Mounts all versioned endpoints for Phase 1 & Phase 2.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    deliveries,
    health,
    locations,
    organizations,
    road_network,
    routing,
    telemetry,
    weather,
    optimization,
    dispatch,
    users,
    vehicles,
)

api_router = APIRouter()

# Phase 1
api_router.include_router(health.router, tags=["Health"])

# Phase 2 — Authentication & Core Logistics Data
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["Vehicles"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
api_router.include_router(deliveries.router, prefix="/deliveries", tags=["Deliveries"])

# Phase 3 — Road Network Graph & Ingestion (Physical Regional Infrastructure)
api_router.include_router(road_network.router, prefix="/road-network", tags=["Road Network"])

# Phase 4 — Multi-Objective Routing Optimization
api_router.include_router(routing.router, prefix="/routing", tags=["Routing"])

# Phase 6 — Live Telemetry, Weather, Fleet Optimization & Dispatch
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
api_router.include_router(weather.router, prefix="/weather", tags=["Weather & Hazards"])
api_router.include_router(optimization.router, prefix="/optimization", tags=["Fleet Optimization"])
api_router.include_router(dispatch.router, prefix="/dispatch", tags=["Dispatch Operations"])


