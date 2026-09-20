"""
RouteIQ 2.0 - FastAPI Application Entrypoint
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.api.v1.endpoints.health import get_health, HealthResponse

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if settings.LOG_LEVEL == "info" else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("routeiq.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    try:
        from app.graph.seeder import seed_road_network_if_empty
        seed_road_network_if_empty()
    except Exception as e:
        logger.warning(f"Initial road network seed note: {e}")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Cognitive, Graph-Aware Logistics Intelligence Platform for the North Eastern Region",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Set up Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount root endpoints
@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }


# Direct /health endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def direct_health():
    return await get_health()


# Mount versioned API routes (/api/v1/...)
app.include_router(api_router, prefix=settings.API_V1_STR)
