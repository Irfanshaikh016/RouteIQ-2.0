/**
 * RouteIQ 2.0 - Centralized Frontend API Client (Phase 1 & Phase 2)
 * Manages HTTP communication, JWT authentication tokens, and typed REST calls.
 */

export const getApiBaseUrl = (): string => {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
};

// =============================================================================
// Phase 1 Diagnostic Types
// =============================================================================

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

// =============================================================================
// Phase 2 Types: Auth, Organizations, Vehicles, Locations, Deliveries
// =============================================================================

export interface UserProfile {
  id: string;
  organization_id: string;
  email: string;
  full_name: string;
  role: "admin" | "manager" | "operator";
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  user_id: string;
  organization_id: string;
  role: string;
  email: string;
  full_name: string;
}

export interface Organization {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export type VehicleStatus = "available" | "assigned" | "inactive" | "maintenance";

export interface Vehicle {
  id: string;
  organization_id: string;
  vehicle_name: string;
  vehicle_type: string;
  registration_number: string;
  capacity: number;
  capacity_unit: string;
  status: VehicleStatus;
  created_at: string;
  updated_at: string;
}

export interface VehicleInput {
  vehicle_name: string;
  vehicle_type: string;
  registration_number: string;
  capacity: number;
  capacity_unit?: string;
  status?: VehicleStatus;
}

export interface Location {
  id: string;
  organization_id: string;
  name: string;
  address_line?: string | null;
  city: string;
  state: string;
  postal_code?: string | null;
  latitude: number;
  longitude: number;
  created_at: string;
  updated_at: string;
}

export interface LocationInput {
  name: string;
  address_line?: string;
  city: string;
  state: string;
  postal_code?: string;
  latitude: number;
  longitude: number;
}

export type DeliveryPriority = "low" | "normal" | "high" | "urgent";
export type DeliveryStatus = "pending" | "assigned" | "in_transit" | "delivered" | "cancelled";

export interface Delivery {
  id: string;
  organization_id: string;
  reference_number: string;
  pickup_location_id: string;
  delivery_location_id: string;
  priority: DeliveryPriority;
  status: DeliveryStatus;
  package_weight: number;
  package_volume: number;
  requested_delivery_date?: string | null;
  time_window_start?: string | null;
  time_window_end?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DeliveryInput {
  reference_number: string;
  pickup_location_id: string;
  delivery_location_id: string;
  priority?: DeliveryPriority;
  status?: DeliveryStatus;
  package_weight?: number;
  package_volume?: number;
  requested_delivery_date?: string;
  time_window_start?: string;
  time_window_end?: string;
  notes?: string;
}

// =============================================================================
// Client-side Token Persistence Helpers
// =============================================================================

const TOKEN_KEY = "routeiq_token";
const USER_KEY = "routeiq_user";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function getStoredUser(): TokenResponse | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setStoredUser(user: TokenResponse): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function clearStoredAuth(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}

// =============================================================================
// HTTP Request Wrapper
// =============================================================================

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  requiresAuth: boolean = true
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");

  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (requiresAuth) {
    const token = getStoredToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(`${baseUrl}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return {} as T;
  }

  let data;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    if (data && typeof data === "object") {
      if (typeof data.detail === "string") {
        errorDetail = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorDetail = data.detail.map((err: { msg?: string }) => err.msg || JSON.stringify(err)).join("; ");
      }
    }
    throw new Error(errorDetail);
  }

  return data as T;
}

// =============================================================================
// Authentication API
// =============================================================================

export async function registerUser(payload: {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
  role?: "admin" | "manager" | "operator";
}): Promise<TokenResponse> {
  const data = await request<TokenResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  }, false);
  setStoredToken(data.access_token);
  setStoredUser(data);
  return data;
}

export async function loginUser(payload: {
  email: string;
  password: string;
}): Promise<TokenResponse> {
  const data = await request<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  }, false);
  setStoredToken(data.access_token);
  setStoredUser(data);
  return data;
}

export async function logoutUser(): Promise<void> {
  try {
    await request<{ message: string }>("/api/v1/auth/logout", {
      method: "POST",
    });
  } finally {
    clearStoredAuth();
  }
}

export async function getMe(): Promise<UserProfile> {
  return request<UserProfile>("/api/v1/auth/me", { method: "GET" });
}

// =============================================================================
// Organizations API
// =============================================================================

export async function getOrganization(orgId: string): Promise<Organization> {
  return request<Organization>(`/api/v1/organizations/${orgId}`, { method: "GET" });
}

export async function updateOrganization(orgId: string, payload: { name?: string; description?: string }): Promise<Organization> {
  return request<Organization>(`/api/v1/organizations/${orgId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

// =============================================================================
// Vehicles API
// =============================================================================

export async function listVehicles(): Promise<Vehicle[]> {
  return request<Vehicle[]>("/api/v1/vehicles", { method: "GET" });
}

export async function getVehicle(id: string): Promise<Vehicle> {
  return request<Vehicle>(`/api/v1/vehicles/${id}`, { method: "GET" });
}

export async function createVehicle(payload: VehicleInput): Promise<Vehicle> {
  return request<Vehicle>("/api/v1/vehicles", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateVehicle(id: string, payload: Partial<VehicleInput>): Promise<Vehicle> {
  return request<Vehicle>(`/api/v1/vehicles/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteVehicle(id: string): Promise<void> {
  await request<void>(`/api/v1/vehicles/${id}`, { method: "DELETE" });
}

// =============================================================================
// Locations API
// =============================================================================

export async function listLocations(): Promise<Location[]> {
  return request<Location[]>("/api/v1/locations", { method: "GET" });
}

export async function getLocation(id: string): Promise<Location> {
  return request<Location>(`/api/v1/locations/${id}`, { method: "GET" });
}

export async function createLocation(payload: LocationInput): Promise<Location> {
  return request<Location>("/api/v1/locations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateLocation(id: string, payload: Partial<LocationInput>): Promise<Location> {
  return request<Location>(`/api/v1/locations/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteLocation(id: string): Promise<void> {
  await request<void>(`/api/v1/locations/${id}`, { method: "DELETE" });
}

// =============================================================================
// Deliveries API
// =============================================================================

export async function listDeliveries(): Promise<Delivery[]> {
  return request<Delivery[]>("/api/v1/deliveries", { method: "GET" });
}

export async function getDelivery(id: string): Promise<Delivery> {
  return request<Delivery>(`/api/v1/deliveries/${id}`, { method: "GET" });
}

export async function createDelivery(payload: DeliveryInput): Promise<Delivery> {
  return request<Delivery>("/api/v1/deliveries", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateDelivery(id: string, payload: Partial<DeliveryInput>): Promise<Delivery> {
  return request<Delivery>(`/api/v1/deliveries/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteDelivery(id: string): Promise<void> {
  await request<void>(`/api/v1/deliveries/${id}`, { method: "DELETE" });
}

// =============================================================================
// Phase 3 Types: Road Network Graph & Ingestion
// =============================================================================

export interface BoundingBox {
  min_lat: number;
  max_lat: number;
  min_lon: number;
  max_lon: number;
}

export interface RoadTypeStats {
  road_type: string;
  count: number;
  total_length_km: number;
}

export interface NetworkStatsResponse {
  total_nodes: number;
  total_edges: number;
  total_length_km: number;
  weakly_connected_components: number;
  strongly_connected_components: number;
  largest_component_nodes: number;
  largest_component_ratio: number;
  road_type_distribution: RoadTypeStats[];
  bounding_box: BoundingBox | null;
}

export interface NetworkHealthResponse {
  status: "healthy" | "degraded" | "empty";
  total_nodes: number;
  total_edges: number;
  is_connected: boolean;
  isolated_nodes: number;
  dead_ends: number;
  warnings: string[];
}

export interface CorridorWaypoint {
  name: string;
  latitude: number;
  longitude: number;
  state: string;
  elevation_m?: number | null;
}

export interface CorridorResponse {
  id: string;
  name: string;
  national_highway: string;
  states_covered: string[];
  start_point: string;
  end_point: string;
  intermediate_waypoints: CorridorWaypoint[];
  approximate_length_km: number;
  terrain_type: string;
  strategic_notes: string;
}

export interface CorridorListResponse {
  total: number;
  corridors: CorridorResponse[];
}

export interface RoadNode {
  id: string;
  osm_id?: number | null;
  latitude: number;
  longitude: number;
  elevation_m?: number | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface RoadNodeListResponse {
  total: number;
  limit: number;
  offset: number;
  nodes: RoadNode[];
}

export interface RoadEdge {
  id: string;
  osm_way_id?: number | null;
  source_node_id: string;
  target_node_id: string;
  road_name?: string | null;
  road_type: string;
  length_meters: number;
  max_speed_kph?: number | null;
  oneway: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface RoadEdgeListResponse {
  total: number;
  limit: number;
  offset: number;
  edges: RoadEdge[];
}

// =============================================================================
// Road Network API
// =============================================================================

export async function getRoadNetworkStats(): Promise<NetworkStatsResponse> {
  return request<NetworkStatsResponse>("/api/v1/road-network/stats", { method: "GET" });
}

export async function getRoadNetworkHealth(): Promise<NetworkHealthResponse> {
  return request<NetworkHealthResponse>("/api/v1/road-network/health", { method: "GET" });
}

export async function listCorridors(): Promise<CorridorListResponse> {
  return request<CorridorListResponse>("/api/v1/road-network/corridors", { method: "GET" });
}

export async function getCorridor(id: string): Promise<CorridorResponse> {
  return request<CorridorResponse>(`/api/v1/road-network/corridors/${id}`, { method: "GET" });
}

export async function listRoadNodes(params?: {
  min_lat?: number;
  max_lat?: number;
  min_lon?: number;
  max_lon?: number;
  limit?: number;
  offset?: number;
}): Promise<RoadNodeListResponse> {
  const query = new URLSearchParams();
  if (params?.min_lat !== undefined) query.set("min_lat", String(params.min_lat));
  if (params?.max_lat !== undefined) query.set("max_lat", String(params.max_lat));
  if (params?.min_lon !== undefined) query.set("min_lon", String(params.min_lon));
  if (params?.max_lon !== undefined) query.set("max_lon", String(params.max_lon));
  if (params?.limit !== undefined) query.set("limit", String(params.limit));
  if (params?.offset !== undefined) query.set("offset", String(params.offset));
  const queryString = query.toString() ? `?${query.toString()}` : "";
  return request<RoadNodeListResponse>(`/api/v1/road-network/nodes${queryString}`, { method: "GET" });
}

export async function listRoadEdges(params?: {
  road_type?: string;
  min_lat?: number;
  max_lat?: number;
  min_lon?: number;
  max_lon?: number;
  limit?: number;
  offset?: number;
}): Promise<RoadEdgeListResponse> {
  const query = new URLSearchParams();
  if (params?.road_type !== undefined) query.set("road_type", params.road_type);
  if (params?.min_lat !== undefined) query.set("min_lat", String(params.min_lat));
  if (params?.max_lat !== undefined) query.set("max_lat", String(params.max_lat));
  if (params?.min_lon !== undefined) query.set("min_lon", String(params.min_lon));
  if (params?.max_lon !== undefined) query.set("max_lon", String(params.max_lon));
  if (params?.limit !== undefined) query.set("limit", String(params.limit));
  if (params?.offset !== undefined) query.set("offset", String(params.offset));
  const queryString = query.toString() ? `?${query.toString()}` : "";
  return request<RoadEdgeListResponse>(`/api/v1/road-network/edges${queryString}`, { method: "GET" });
}

// =============================================================================
// Phase 4 Types: Multi-Objective Routing Optimization
// =============================================================================

export interface Coordinate {
  latitude: number;
  longitude: number;
}

export interface RouteRequest {
  origin: Coordinate;
  destination: Coordinate;
  profile?: "fastest" | "safest" | "balanced" | string;
  max_nearest_distance_km?: number;
}

export interface RouteCostBreakdown {
  distance_cost: number;
  time_cost: number;
  risk_cost: number;
  terrain_cost: number;
  total_cost: number;
}

export interface RouteRiskBreakdown {
  flood_risk: number;
  landslide_risk: number;
  monsoon_risk: number;
  terrain_risk: number;
  surface_risk: number;
  overall_risk: number;
}

export interface RouteNodeItem {
  sequence: number;
  node_id: string;
  osm_id?: number | null;
  latitude: number;
  longitude: number;
  elevation_m?: number | null;
}

export interface RouteEdgeItem {
  sequence: number;
  edge_id: string;
  osm_way_id?: number | null;
  source_node_id: string;
  target_node_id: string;
  road_name?: string | null;
  road_type: string;
  length_meters: number;
  estimated_time_seconds: number;
  cost_breakdown: RouteCostBreakdown;
  risk_breakdown: RouteRiskBreakdown;
}

export interface RouteMetrics {
  distance_km: number;
  estimated_time_minutes: number;
  objective_score: number;
  risk_score: number;
  terrain_score: number;
}

export interface GeoJSONLineString {
  type: "LineString";
  coordinates: [number, number][]; // [longitude, latitude]
}

export interface RouteProfileInfo {
  name: string;
  description: string;
  weights: {
    distance_weight: number;
    time_weight: number;
    risk_weight: number;
    terrain_weight: number;
  };
  trade_offs: string;
}

export interface RouteResponse {
  route_id: string;
  profile: string;
  origin: Coordinate;
  destination: Coordinate;
  metrics: RouteMetrics;
  nodes: RouteNodeItem[];
  edges: RouteEdgeItem[];
  geometry: GeoJSONLineString;
  optimization_metadata: Record<string, unknown>;
}

export interface RoutingProfilesResponse {
  total: number;
  profiles: RouteProfileInfo[];
}

export interface RoutingHealthResponse {
  status: "healthy" | "degraded" | "empty";
  engine_version: string;
  graph_available: boolean;
  total_nodes: number;
  total_edges: number;
  profiles_loaded: string[];
}

export interface RouteComparisonResponse {
  origin: Coordinate;
  destination: Coordinate;
  routes: RouteResponse[];
}

// =============================================================================
// Routing API Functions
// =============================================================================

export async function calculateRoute(payload: RouteRequest): Promise<RouteResponse> {
  return request<RouteResponse>("/api/v1/routing/route", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function compareRoutes(payload: RouteRequest): Promise<RouteComparisonResponse> {
  return request<RouteComparisonResponse>("/api/v1/routing/compare", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getRoutingProfiles(): Promise<RoutingProfilesResponse> {
  return request<RoutingProfilesResponse>("/api/v1/routing/profiles", { method: "GET" });
}

export async function getRoutingHealth(): Promise<RoutingHealthResponse> {
  return request<RoutingHealthResponse>("/api/v1/routing/health", { method: "GET" });
}


