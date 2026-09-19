"""
RouteIQ 2.0 - Vehicle Telemetry Endpoints (Phase 6)
Provides GPS ingestion, real-time fleet state tracking, and tenant-scoped telemetry queries.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from app.core.dependencies import get_current_org_id, get_current_user
from app.core.security import decode_access_token
from app.telemetry.exceptions import (
    CrossTenantTelemetryError,
    InvalidTelemetryError,
    VehicleNotFoundError,
)
from app.telemetry.schemas import (
    FleetTelemetrySummary,
    TelemetryHealthResponse,
    TelemetryIngestRequest,
    VehicleStateResponse,
    VehicleTelemetryResponse,
)
from app.telemetry.service import TelemetryService, get_telemetry_service

router = APIRouter()


@router.post("", response_model=VehicleTelemetryResponse, status_code=status.HTTP_201_CREATED)
async def ingest_telemetry(
    payload: TelemetryIngestRequest,
    org_id: str = Depends(get_current_org_id),
    service: TelemetryService = Depends(get_telemetry_service),
) -> VehicleTelemetryResponse:
    """
    Ingests a live or simulated vehicle GPS telemetry ping.
    Validates coordinates, speed, and enforces strict tenant ownership.
    """
    try:
        return service.ingest_telemetry(org_id, payload)
    except VehicleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CrossTenantTelemetryError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except (InvalidTelemetryError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/vehicles/{vehicle_id}", response_model=VehicleStateResponse)
async def get_vehicle_telemetry(
    vehicle_id: str,
    org_id: str = Depends(get_current_org_id),
    service: TelemetryService = Depends(get_telemetry_service),
) -> VehicleStateResponse:
    """Retrieves real-time telemetry state and freshness indicator for a specific vehicle."""
    try:
        return service.get_vehicle_state(org_id, vehicle_id)
    except VehicleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CrossTenantTelemetryError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/fleet", response_model=FleetTelemetrySummary)
async def get_fleet_telemetry(
    org_id: str = Depends(get_current_org_id),
    service: TelemetryService = Depends(get_telemetry_service),
) -> FleetTelemetrySummary:
    """Retrieves fleet-wide telemetry summary and vehicle freshness breakdown for the tenant."""
    return service.get_fleet_state(org_id)


@router.get("/health", response_model=TelemetryHealthResponse)
async def get_telemetry_health(
    service: TelemetryService = Depends(get_telemetry_service),
) -> TelemetryHealthResponse:
    """Telemetry ingestion health and diagnostic metrics."""
    return service.get_health()


@router.websocket("/ws")
async def telemetry_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    service: TelemetryService = Depends(get_telemetry_service),
):
    """
    Real-time telemetry WebSocket streaming channel.
    Authenticates token, enforces organization boundaries, and pushes live fleet state updates.
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = decode_access_token(token)
        org_id = payload.get("org_id")
        if not org_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    try:
        # Push initial fleet state
        fleet_state = service.get_fleet_state(org_id)
        await websocket.send_json(fleet_state.model_dump(mode="json"))

        # Keep connection open for incoming messages / heartbeats
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "refresh":
                fleet_state = service.get_fleet_state(org_id)
                await websocket.send_json(fleet_state.model_dump(mode="json"))
    except WebSocketDisconnect:
        pass
