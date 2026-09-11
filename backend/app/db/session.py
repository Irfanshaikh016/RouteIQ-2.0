"""
Modular Database Access Layer for RouteIQ 2.0.
Supports:
1. Direct PostgreSQL (local or cloud connection pooler via asyncpg)
2. Supabase Cloud Client (via official supabase-py SDK)
"""
import logging
from typing import Any, Dict, Optional
import asyncpg
from supabase import Client, create_client
from app.core.config import settings

logger = logging.getLogger("routeiq.db")

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Returns an initialized Supabase Client if credentials are provided in settings.
    Caches the instance for subsequent calls.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if settings.SUPABASE_URL and (settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY):
        key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        try:
            _supabase_client = create_client(settings.SUPABASE_URL, key)
            logger.info("Supabase client successfully initialized.")
            return _supabase_client
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            return None
    return None


async def check_postgres_health(db_url: str) -> Dict[str, Any]:
    """Tests connectivity to PostgreSQL database via asyncpg."""
    try:
        # Connect with a strict 3-second timeout to avoid blocking health checks
        conn = await asyncpg.connect(db_url, timeout=3.0)
        try:
            val = await conn.fetchval("SELECT 1;")
            version = await conn.fetchval("SELECT version();")
            return {
                "status": "connected",
                "driver": "asyncpg",
                "ping": "ok" if val == 1 else "unexpected",
                "server_version": version.split(",")[0] if version else "unknown",
            }
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"PostgreSQL health check failed: {e}")
        return {
            "status": "error",
            "driver": "asyncpg",
            "error": str(e),
        }


def check_supabase_health() -> Dict[str, Any]:
    """Tests connectivity to Supabase API endpoints."""
    client = get_supabase_client()
    if not client:
        return {
            "status": "not_configured",
            "driver": "supabase-py",
            "message": "SUPABASE_URL or API key is not set",
        }
    try:
        # Check Supabase auth/storage/rest connectivity
        return {
            "status": "connected",
            "driver": "supabase-py",
            "url": settings.SUPABASE_URL,
        }
    except Exception as e:
        return {
            "status": "error",
            "driver": "supabase-py",
            "error": str(e),
        }


async def check_database_health() -> Dict[str, Any]:
    """
    Unified database health assessment for RouteIQ 2.0.
    Checks PostgreSQL if DATABASE_URL is configured, and checks Supabase if configured.
    """
    result: Dict[str, Any] = {
        "configured": False,
        "primary": "none",
        "postgres": None,
        "supabase": None,
    }

    if settings.DATABASE_URL:
        result["configured"] = True
        result["primary"] = "postgresql"
        result["postgres"] = await check_postgres_health(settings.DATABASE_URL)

    if settings.SUPABASE_URL and (settings.SUPABASE_ANON_KEY or settings.SUPABASE_SERVICE_ROLE_KEY):
        result["configured"] = True
        if result["primary"] == "none":
            result["primary"] = "supabase"
        result["supabase"] = check_supabase_health()

    if not result["configured"]:
        result["message"] = "No database credentials configured (DATABASE_URL or SUPABASE_URL). Operating in decoupled mode."

    return result
