"""
RouteIQ 2.0 - Core Multi-Tenant Repository Store (Phase 2)
Provides organization-scoped storage for Users, Organizations, Vehicles, Locations, and Deliveries.
Guarantees tenant isolation: Every query for logistics data enforces organization_id boundaries.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
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

    def clear(self):
        """Clears all in-memory entities. Useful for test isolation."""
        self.organizations.clear()
        self.users.clear()
        self.vehicles.clear()
        self.locations.clear()
        self.deliveries.clear()

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


# Global singleton instance
_store = DataStore()


def get_store() -> DataStore:
    """Returns global DataStore instance."""
    return _store
