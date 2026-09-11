/**
 * RouteIQ 2.0 - Frontend API Client
 * Manages communication with the FastAPI backend.
 */

export interface DatabaseHealth {
  configured: boolean;
  primary: string;
  postgres?: {
    status: string;
    driver?: string;
    ping?: string;
    server_version?: string;
    error?: string;
  } | null;
  supabase?: {
    status: string;
    driver?: string;
    url?: string;
    error?: string;
  } | null;
  message?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  database: DatabaseHealth;
}

export interface ApiPingResult {
  ok: boolean;
  statusCode?: number;
  latencyMs: number;
  data?: HealthResponse;
  error?: string;
}

export const getApiBaseUrl = (): string => {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
};

export async function checkBackendHealth(): Promise<ApiPingResult> {
  const baseUrl = getApiBaseUrl();
  const startTime = performance.now();

  try {
    const response = await fetch(`${baseUrl}/health`, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    const latencyMs = Math.round(performance.now() - startTime);

    if (!response.ok) {
      return {
        ok: false,
        statusCode: response.status,
        latencyMs,
        error: `HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const data: HealthResponse = await response.json();
    return {
      ok: true,
      statusCode: response.status,
      latencyMs,
      data,
    };
  } catch (err: unknown) {
    const latencyMs = Math.round(performance.now() - startTime);
    const message = err instanceof Error ? err.message : "Unknown network error";
    return {
      ok: false,
      latencyMs,
      error: `Connection to backend failed (${baseUrl}): ${message}`,
    };
  }
}
