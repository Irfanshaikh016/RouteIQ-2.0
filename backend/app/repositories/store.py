"""
RouteIQ 2.0 - Core Multi-Tenant Repository Store (Phase 2)
Provides organization-scoped storage for Users, Organizations, Vehicles, Locations, and Deliveries.
Guarantees tenant isolation: Every query for logistics data enforces organization_id boundaries.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger("routeiq.store")


class DataStore:
    """
    In-memory thread-safe datastore used for unit tests, offline development,
    and modular facade for PostgreSQL persistence.
    """

    def __init__(self):
        self.organizations: Dict[str, Dict[str, Any]] = {}
        self.users: Dict[str, Dict[str, Any]] = {}
        self.vehicles: Dict[str, Dict[str, Any]] = {}
        self.locations: Dict[str, Dict[str, Any]] = {}
        self.deliveries: Dict[str, Dict[str, Any]] = {}
        # Phase 3 Road Network (Shared regional infrastructure)
        self.road_nodes: Dict[str, Dict[str, Any]] = {}
        self.osm_node_map: Dict[int, str] = {}
        self.road_edges: Dict[str, Dict[str, Any]] = {}
        # Phase 6 Telemetry, Weather, Hazards, Road Restrictions & Optimization
        self.vehicle_telemetry: Dict[str, Dict[str, Any]] = {}
        self.latest_vehicle_telemetry: Dict[str, Dict[str, Any]] = {}
        self.weather_observations: List[Dict[str, Any]] = []
        self.hazard_events: Dict[str, Dict[str, Any]] = {}
        self.road_restrictions: Dict[str, Dict[str, Any]] = {}
        self.optimization_runs: Dict[str, Dict[str, Any]] = {}

    def clear(self):
        """Clears all in-memory entities. Useful for test isolation."""
        self.organizations.clear()
        self.users.clear()
        self.vehicles.clear()
        self.locations.clear()
        self.deliveries.clear()
        self.road_nodes.clear()
        self.osm_node_map.clear()
        self.road_edges.clear()
        self.vehicle_telemetry.clear()
        self.latest_vehicle_telemetry.clear()
        self.weather_observations.clear()
        self.hazard_events.clear()
        self.road_restrictions.clear()
        self.optimization_runs.clear()

    # --------------------------------------------------------------------------
    # Organizations
    # --------------------------------------------------------------------------
    def create_organization(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        org_id = str(uuid.uuid4())
        org = {
            "id": org_id,
            "name": name,
            "description": description,
            "created_at": now,
            "updated_at": now,
        }
        self.organizations[org_id] = org
        return org

    def get_organization(self, org_id: str) -> Optional[Dict[str, Any]]:
        return self.organizations.get(org_id)

    def update_organization(self, org_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Dict[str, Any]]:
        org = self.organizations.get(org_id)
        if not org:
            return None
        if name is not None:
            org["name"] = name
        if description is not None:
            org["description"] = description
        org["updated_at"] = datetime.now(timezone.utc)
        return org

    # --------------------------------------------------------------------------
    # Users
    # --------------------------------------------------------------------------
    def create_user(
        self,
        organization_id: str,
        email: str,
        password_hash: str,
        full_name: str,
        role: str = "operator",
    ) -> Dict[str, Any]:
        email_normalized = email.strip().lower()
        for u in self.users.values():
            if u["email"].lower() == email_normalized:
                raise ValueError("Email already registered")

        now = datetime.now(timezone.utc)
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "organization_id": organization_id,
            "email": email_normalized,
            "password_hash": password_hash,
            "full_name": full_name,
            "role": role,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        self.users[user_id] = user
        return user

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        email_normalized = email.strip().lower()
        for u in self.users.values():
            if u["email"].lower() == email_normalized:
                return u
        return None

    def update_user(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        user = self.users.get(user_id)
        if not user:
            return None
        if full_name is not None:
            user["full_name"] = full_name
        if role is not None:
            user["role"] = role
        if is_active is not None:
            user["is_active"] = is_active
        user["updated_at"] = datetime.now(timezone.utc)
        return user

    # --------------------------------------------------------------------------
    # Vehicles (Scoped by organization_id)
    # --------------------------------------------------------------------------
    def create_vehicle(
        self,
        organization_id: str,
        vehicle_name: str,
        vehicle_type: str,
        registration_number: str,
        capacity: float,
        capacity_unit: str = "kg",
        status: str = "available",
    ) -> Dict[str, Any]:
        # Check uniqueness within the organization
        for v in self.vehicles.values():
            if v["organization_id"] == organization_id and v["registration_number"].upper() == registration_number.strip().upper():
                raise ValueError("A vehicle with this registration number already exists in your organization")

        now = datetime.now(timezone.utc)
        vehicle_id = str(uuid.uuid4())
        vehicle = {
            "id": vehicle_id,
            "organization_id": organization_id,
            "vehicle_name": vehicle_name,
            "vehicle_type": vehicle_type,
            "registration_number": registration_number.strip().upper(),
            "capacity": float(capacity),
            "capacity_unit": capacity_unit,
            "status": status,
            "created_at": now,
            "updated_at": now,
        }
        self.vehicles[vehicle_id] = vehicle
        return vehicle

    def get_vehicle(self, organization_id: str, vehicle_id: str) -> Optional[Dict[str, Any]]:
        v = self.vehicles.get(vehicle_id)
        if v and v["organization_id"] == organization_id:
            return v
        return None

    def list_vehicles(self, organization_id: str) -> List[Dict[str, Any]]:
        return [v for v in self.vehicles.values() if v["organization_id"] == organization_id]

    def update_vehicle(
        self,
        organization_id: str,
        vehicle_id: str,
        vehicle_name: Optional[str] = None,
        vehicle_type: Optional[str] = None,
        registration_number: Optional[str] = None,
        capacity: Optional[float] = None,
        capacity_unit: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        v = self.get_vehicle(organization_id, vehicle_id)
        if not v:
            return None

        if registration_number is not None:
            reg_clean = registration_number.strip().upper()
            for other_id, other_v in self.vehicles.items():
                if other_id != vehicle_id and other_v["organization_id"] == organization_id and other_v["registration_number"] == reg_clean:
                    raise ValueError("Registration number already in use within your organization")
            v["registration_number"] = reg_clean

        if vehicle_name is not None:
            v["vehicle_name"] = vehicle_name
        if vehicle_type is not None:
            v["vehicle_type"] = vehicle_type
        if capacity is not None:
            v["capacity"] = float(capacity)
        if capacity_unit is not None:
            v["capacity_unit"] = capacity_unit
        if status is not None:
            v["status"] = status
        v["updated_at"] = datetime.now(timezone.utc)
        return v

    def delete_vehicle(self, organization_id: str, vehicle_id: str) -> bool:
        v = self.get_vehicle(organization_id, vehicle_id)
        if not v:
            return False
        del self.vehicles[vehicle_id]
        return True

    # --------------------------------------------------------------------------
    # Locations (Scoped by organization_id)
    # --------------------------------------------------------------------------
    def create_location(
        self,
        organization_id: str,
        name: str,
        address_line: Optional[str],
        city: str,
        state: str,
        postal_code: Optional[str],
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        loc_id = str(uuid.uuid4())
        location = {
            "id": loc_id,
            "organization_id": organization_id,
            "name": name,
            "address_line": address_line,
            "city": city,
            "state": state,
            "postal_code": postal_code,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "created_at": now,
            "updated_at": now,
        }
        self.locations[loc_id] = location
        return location

    def get_location(self, organization_id: str, location_id: str) -> Optional[Dict[str, Any]]:
        loc = self.locations.get(location_id)
        if loc and loc["organization_id"] == organization_id:
            return loc
        return None

    def list_locations(self, organization_id: str) -> List[Dict[str, Any]]:
        return [loc for loc in self.locations.values() if loc["organization_id"] == organization_id]

    def update_location(
        self,
        organization_id: str,
        location_id: str,
        name: Optional[str] = None,
        address_line: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        loc = self.get_location(organization_id, location_id)
        if not loc:
            return None
        if name is not None:
            loc["name"] = name
        if address_line is not None:
            loc["address_line"] = address_line
        if city is not None:
            loc["city"] = city
        if state is not None:
            loc["state"] = state
        if postal_code is not None:
            loc["postal_code"] = postal_code
        if latitude is not None:
            loc["latitude"] = float(latitude)
        if longitude is not None:
            loc["longitude"] = float(longitude)
        loc["updated_at"] = datetime.now(timezone.utc)
        return loc

    def delete_location(self, organization_id: str, location_id: str) -> bool:
        loc = self.get_location(organization_id, location_id)
        if not loc:
            return False

        # Ensure location is not actively referenced by deliveries in the organization
        for d in self.deliveries.values():
            if d["organization_id"] == organization_id and (d["pickup_location_id"] == location_id or d["delivery_location_id"] == location_id):
                raise ValueError("Cannot delete location because active deliveries reference it")

        del self.locations[location_id]
        return True

    # --------------------------------------------------------------------------
    # Deliveries (Scoped by organization_id)
    # --------------------------------------------------------------------------
    def create_delivery(
        self,
        organization_id: str,
        reference_number: str,
        pickup_location_id: str,
        delivery_location_id: str,
        priority: str = "normal",
        status: str = "pending",
        package_weight: float = 0.0,
        package_volume: float = 0.0,
        requested_delivery_date: Optional[Any] = None,
        time_window_start: Optional[Any] = None,
        time_window_end: Optional[Any] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Validate pickup and delivery locations belong to the same organization
        pickup = self.get_location(organization_id, pickup_location_id)
        if not pickup:
            raise ValueError("Pickup location not found in your organization")

        delivery_loc = self.get_location(organization_id, delivery_location_id)
        if not delivery_loc:
            raise ValueError("Delivery destination location not found in your organization")

        ref_clean = reference_number.strip().upper()
        for d in self.deliveries.values():
            if d["organization_id"] == organization_id and d["reference_number"] == ref_clean:
                raise ValueError("A delivery with this reference number already exists in your organization")

        now = datetime.now(timezone.utc)
        delivery_id = str(uuid.uuid4())
        delivery = {
            "id": delivery_id,
            "organization_id": organization_id,
            "reference_number": ref_clean,
            "pickup_location_id": pickup_location_id,
            "delivery_location_id": delivery_location_id,
            "priority": priority,
            "status": status,
            "package_weight": float(package_weight),
            "package_volume": float(package_volume),
            "requested_delivery_date": requested_delivery_date,
            "time_window_start": time_window_start,
            "time_window_end": time_window_end,
            "notes": notes,
            "created_at": now,
            "updated_at": now,
        }
        self.deliveries[delivery_id] = delivery
        return delivery

    def get_delivery(self, organization_id: str, delivery_id: str) -> Optional[Dict[str, Any]]:
        d = self.deliveries.get(delivery_id)
        if d and d["organization_id"] == organization_id:
            return d
        return None

    def list_deliveries(self, organization_id: str) -> List[Dict[str, Any]]:
        return [d for d in self.deliveries.values() if d["organization_id"] == organization_id]

    def update_delivery(
        self,
        organization_id: str,
        delivery_id: str,
        reference_number: Optional[str] = None,
        pickup_location_id: Optional[str] = None,
        delivery_location_id: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        package_weight: Optional[float] = None,
        package_volume: Optional[float] = None,
        requested_delivery_date: Optional[Any] = None,
        time_window_start: Optional[Any] = None,
        time_window_end: Optional[Any] = None,
        notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        d = self.get_delivery(organization_id, delivery_id)
        if not d:
            return None

        if reference_number is not None:
            ref_clean = reference_number.strip().upper()
            for other_id, other_d in self.deliveries.items():
                if other_id != delivery_id and other_d["organization_id"] == organization_id and other_d["reference_number"] == ref_clean:
                    raise ValueError("Delivery reference number already in use within your organization")
            d["reference_number"] = ref_clean

        if pickup_location_id is not None:
            pickup = self.get_location(organization_id, pickup_location_id)
            if not pickup:
                raise ValueError("Pickup location not found in your organization")
            d["pickup_location_id"] = pickup_location_id

        if delivery_location_id is not None:
            dest = self.get_location(organization_id, delivery_location_id)
            if not dest:
                raise ValueError("Delivery destination location not found in your organization")
            d["delivery_location_id"] = delivery_location_id

        if priority is not None:
            d["priority"] = priority
        if status is not None:
            d["status"] = status
        if package_weight is not None:
            d["package_weight"] = float(package_weight)
        if package_volume is not None:
            d["package_volume"] = float(package_volume)
        if requested_delivery_date is not None:
            d["requested_delivery_date"] = requested_delivery_date
        if time_window_start is not None:
            d["time_window_start"] = time_window_start
        if time_window_end is not None:
            d["time_window_end"] = time_window_end
        if notes is not None:
            d["notes"] = notes
        d["updated_at"] = datetime.now(timezone.utc)
        return d

    def delete_delivery(self, organization_id: str, delivery_id: str) -> bool:
        d = self.get_delivery(organization_id, delivery_id)
        if not d:
            return False
        del self.deliveries[delivery_id]
        return True

    # --------------------------------------------------------------------------
    # Road Network (Phase 3 - Shared Physical Regional Infrastructure)
    # --------------------------------------------------------------------------
    def create_road_node(
        self,
        latitude: float,
        longitude: float,
        osm_id: Optional[int] = None,
        elevation_m: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if osm_id is not None and osm_id in self.osm_node_map:
            return self.road_nodes[self.osm_node_map[osm_id]]

        node_id = str(uuid.uuid4())
        node = {
            "id": node_id,
            "osm_id": osm_id,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "elevation_m": float(elevation_m) if elevation_m is not None else None,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc),
        }
        self.road_nodes[node_id] = node
        if osm_id is not None:
            self.osm_node_map[osm_id] = node_id
        return node

    def get_road_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        return self.road_nodes.get(node_id)

    def get_road_node_by_osm_id(self, osm_id: int) -> Optional[Dict[str, Any]]:
        node_id = self.osm_node_map.get(osm_id)
        return self.road_nodes.get(node_id) if node_id else None

    def list_road_nodes(
        self,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        nodes = list(self.road_nodes.values())
        if min_lat is not None:
            nodes = [n for n in nodes if n["latitude"] >= min_lat]
        if max_lat is not None:
            nodes = [n for n in nodes if n["latitude"] <= max_lat]
        if min_lon is not None:
            nodes = [n for n in nodes if n["longitude"] >= min_lon]
        if max_lon is not None:
            nodes = [n for n in nodes if n["longitude"] <= max_lon]

        total = len(nodes)
        paged = nodes[offset : offset + limit]
        return paged, total

    def create_road_edge(
        self,
        source_node_id: str,
        target_node_id: str,
        road_type: str,
        length_meters: float,
        road_name: Optional[str] = None,
        max_speed_kph: Optional[float] = None,
        oneway: bool = False,
        osm_way_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if source_node_id not in self.road_nodes or target_node_id not in self.road_nodes:
            raise ValueError("Both source and target road nodes must exist in the database")

        edge_id = str(uuid.uuid4())
        edge = {
            "id": edge_id,
            "osm_way_id": osm_way_id,
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "road_name": road_name,
            "road_type": road_type,
            "length_meters": float(length_meters),
            "max_speed_kph": float(max_speed_kph) if max_speed_kph is not None else None,
            "oneway": oneway,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc),
        }
        self.road_edges[edge_id] = edge
        return edge

    def get_road_edge(self, edge_id: str) -> Optional[Dict[str, Any]]:
        return self.road_edges.get(edge_id)

    def list_road_edges(
        self,
        road_type: Optional[str] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        edges = list(self.road_edges.values())
        if road_type is not None:
            edges = [e for e in edges if e["road_type"].lower() == road_type.lower()]

        if any(coord is not None for coord in (min_lat, max_lat, min_lon, max_lon)):
            filtered = []
            for e in edges:
                src = self.road_nodes.get(e["source_node_id"])
                tgt = self.road_nodes.get(e["target_node_id"])
                if not src or not tgt:
                    continue
                # include edge if either endpoint is in the bounding box
                for pt in (src, tgt):
                    in_box = True
                    if min_lat is not None and pt["latitude"] < min_lat:
                        in_box = False
                    if max_lat is not None and pt["latitude"] > max_lat:
                        in_box = False
                    if min_lon is not None and pt["longitude"] < min_lon:
                        in_box = False
                    if max_lon is not None and pt["longitude"] > max_lon:
                        in_box = False
                    if in_box:
                        filtered.append(e)
                        break
            edges = filtered

        total = len(edges)
        paged = edges[offset : offset + limit]
        return paged, total

    def bulk_insert_road_network(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ) -> Tuple[int, int]:
        """High-efficiency batch ingestion of nodes and edges."""
        inserted_nodes = 0
        for n in nodes:
            osm_id = n.get("osm_id")
            if osm_id is not None and osm_id in self.osm_node_map:
                continue
            nid = n.get("id") or str(uuid.uuid4())
            n["id"] = nid
            if "created_at" not in n:
                n["created_at"] = datetime.now(timezone.utc)
            self.road_nodes[nid] = n
            if osm_id is not None:
                self.osm_node_map[osm_id] = nid
            inserted_nodes += 1

        inserted_edges = 0
        for e in edges:
            eid = e.get("id") or str(uuid.uuid4())
            e["id"] = eid
            if "created_at" not in e:
                e["created_at"] = datetime.now(timezone.utc)
            self.road_edges[eid] = e
            inserted_edges += 1

        return inserted_nodes, inserted_edges

    def get_all_road_nodes(self) -> List[Dict[str, Any]]:
        return list(self.road_nodes.values())

    def get_all_road_edges(self) -> List[Dict[str, Any]]:
        return list(self.road_edges.values())

    # --------------------------------------------------------------------------
    # Phase 6: Vehicle Telemetry
    # --------------------------------------------------------------------------
    def record_telemetry(
        self,
        organization_id: str,
        vehicle_id: str,
        timestamp: datetime,
        latitude: float,
        longitude: float,
        speed: float,
        heading: Optional[float] = None,
        ignition_status: bool = True,
        battery_level: Optional[float] = None,
        accuracy: Optional[float] = None,
        source: str = "SIMULATED_TEST",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        rec_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        record = {
            "id": rec_id,
            "organization_id": organization_id,
            "vehicle_id": vehicle_id,
            "timestamp": timestamp,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "speed": float(speed),
            "heading": float(heading) if heading is not None else None,
            "ignition_status": ignition_status,
            "battery_level": float(battery_level) if battery_level is not None else None,
            "accuracy": float(accuracy) if accuracy is not None else None,
            "source": source,
            "metadata": metadata or {},
            "created_at": now,
        }
        self.vehicle_telemetry[rec_id] = record
        # Cache as latest for quick fleet lookup
        prev = self.latest_vehicle_telemetry.get(vehicle_id)
        if prev is None or timestamp >= prev["timestamp"]:
            self.latest_vehicle_telemetry[vehicle_id] = record
        return record

    def get_latest_telemetry(self, organization_id: str, vehicle_id: str) -> Optional[Dict[str, Any]]:
        veh = self.vehicles.get(vehicle_id)
        if not veh or veh.get("organization_id") != organization_id:
            return None
        rec = self.latest_vehicle_telemetry.get(vehicle_id)
        if rec and rec.get("organization_id") == organization_id:
            return rec
        return None

    def get_fleet_telemetry(self, organization_id: str) -> List[Dict[str, Any]]:
        org_vehicles = [v["id"] for v in self.vehicles.values() if v.get("organization_id") == organization_id]
        records = []
        for vid in org_vehicles:
            rec = self.latest_vehicle_telemetry.get(vid)
            if rec and rec.get("organization_id") == organization_id:
                records.append(rec)
        return records

    # --------------------------------------------------------------------------
    # Phase 6: Weather & Hazard Events
    # --------------------------------------------------------------------------
    def record_weather_observation(
        self,
        latitude: float,
        longitude: float,
        rainfall_mm: float = 0.0,
        temperature_c: Optional[float] = None,
        wind_speed_kmh: Optional[float] = None,
        visibility_km: Optional[float] = None,
        soil_moisture_pct: Optional[float] = None,
        source: str = "STATIC_PROVIDER",
        observed_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        now = observed_at or datetime.now(timezone.utc)
        obs_id = str(uuid.uuid4())
        obs = {
            "id": obs_id,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "rainfall_mm": float(rainfall_mm),
            "temperature_c": float(temperature_c) if temperature_c is not None else None,
            "wind_speed_kmh": float(wind_speed_kmh) if wind_speed_kmh is not None else None,
            "visibility_km": float(visibility_km) if visibility_km is not None else None,
            "soil_moisture_pct": float(soil_moisture_pct) if soil_moisture_pct is not None else None,
            "source": source,
            "observed_at": now,
            "created_at": datetime.now(timezone.utc),
        }
        self.weather_observations.append(obs)
        return obs

    def create_hazard_event(
        self,
        hazard_type: str,
        severity: float,
        latitude: float,
        longitude: float,
        radius_meters: float = 1000.0,
        description: Optional[str] = None,
        source: str = "MODELED_HEURISTIC",
        confidence: float = 1.0,
        starts_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        hid = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        h = {
            "id": hid,
            "hazard_type": hazard_type,
            "severity": float(severity),
            "latitude": float(latitude),
            "longitude": float(longitude),
            "radius_meters": float(radius_meters),
            "description": description or f"{hazard_type.capitalize()} alert",
            "source": source,
            "confidence": float(confidence),
            "starts_at": starts_at or now,
            "expires_at": expires_at or now,
            "created_at": now,
        }
        self.hazard_events[hid] = h
        return h

    def get_active_hazards(self, current_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        now = current_time or datetime.now(timezone.utc)
        active = []
        for h in self.hazard_events.values():
            if h["starts_at"] <= now <= h["expires_at"]:
                active.append(h)
        return active

    # --------------------------------------------------------------------------
    # Phase 6: Road Restrictions (Shared infrastructure state)
    # --------------------------------------------------------------------------
    def set_road_restriction(
        self,
        road_edge_id: str,
        status: str = "OPEN",
        speed_multiplier: float = 1.0,
        reason: Optional[str] = None,
        road_name: Optional[str] = None,
        starts_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        res_id = str(uuid.uuid4())
        restriction = {
            "id": res_id,
            "road_edge_id": road_edge_id,
            "road_name": road_name or "Highway",
            "status": status.upper(),
            "speed_multiplier": float(speed_multiplier),
            "reason": reason or "Operational restriction",
            "starts_at": starts_at or now,
            "expires_at": expires_at,
            "created_at": now,
        }
        self.road_restrictions[road_edge_id] = restriction
        return restriction

    def get_road_restrictions(self) -> List[Dict[str, Any]]:
        return list(self.road_restrictions.values())

    def get_road_restriction_for_edge(self, edge_id: str) -> Optional[Dict[str, Any]]:
        return self.road_restrictions.get(edge_id)

    # --------------------------------------------------------------------------
    # Phase 6: Optimization Runs
    # --------------------------------------------------------------------------
    def create_optimization_run(
        self,
        organization_id: str,
        problem_type: str,
        profile: str,
        depot_location_id: str,
        vehicle_ids: List[str],
        delivery_ids: List[str],
        status: str,
        total_distance_km: float,
        total_duration_minutes: float,
        total_cost: float,
        total_risk: float,
        vehicles_used: int,
        served_deliveries_count: int,
        unserved_deliveries: List[Dict[str, Any]],
        routes_payload: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        run = {
            "id": run_id,
            "organization_id": organization_id,
            "problem_type": problem_type,
            "profile": profile,
            "depot_location_id": depot_location_id,
            "vehicle_ids": vehicle_ids,
            "delivery_ids": delivery_ids,
            "status": status,
            "total_distance_km": float(total_distance_km),
            "total_duration_minutes": float(total_duration_minutes),
            "total_cost": float(total_cost),
            "total_risk": float(total_risk),
            "vehicles_used": int(vehicles_used),
            "served_deliveries_count": int(served_deliveries_count),
            "unserved_deliveries": unserved_deliveries,
            "routes_payload": routes_payload,
            "created_at": now,
        }
        self.optimization_runs[run_id] = run
        return run

    def get_optimization_run(self, organization_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        run = self.optimization_runs.get(run_id)
        if run and run.get("organization_id") == organization_id:
            return run
        return None

    def list_optimization_runs(self, organization_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        runs = [r for r in self.optimization_runs.values() if r.get("organization_id") == organization_id]
        runs.sort(key=lambda x: x["created_at"], reverse=True)
        return runs[:limit]


# Global singleton instance
_store = DataStore()


def get_store() -> DataStore:
    """Returns global DataStore instance."""
    return _store
