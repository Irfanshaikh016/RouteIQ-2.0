# RouteIQ 2.0 — Map Architecture & Cartography Guide

## 1. Technical Design Decisions

### 1.1 Why Leaflet instead of Mapbox GL?
1. **Zero External API Tokens**: No credit card or `NEXT_PUBLIC_MAPBOX_TOKEN` required for development, evaluation, or production deployment.
2. **Open Source & Light Footprint**: High-performance raster and vector graphics handling with pure open-source packages (`leaflet`, `@types/leaflet`).
3. **Resilience**: Operates in self-contained offline and intranet environments without mandatory third-party telemetry.

### 1.2 SSR Safety Strategy in Next.js 16
Leaflet directly manipulates the browser's `window` and `document` DOM APIs. During Next.js 16 server-side compilation, importing Leaflet triggers fatal `window is not defined` errors.

**Solution implemented in `MapWrapper.tsx`**:
```tsx
const RouteIQMap = dynamic(() => import("./RouteIQMap"), {
  ssr: false,
  loading: () => <LoadingSkeleton />,
});
```

### 1.3 Coordinate Mapping & GeoJSON Handling
- **GeoJSON Standard**: Coordinates are formatted as `[longitude, latitude]` (e.g. `[91.8210, 26.1158]`).
- **Leaflet Native**: Polylines and markers expect `[latitude, longitude]` (e.g. `[26.1158, 91.8210]`).
- **Conversion**: `RouteIQMap` maps all GeoJSON coordinate tuples via `coords.map(c => [c[1], c[0]])` prior to instantiating `L.polyline` and `L.marker`.

---

## 2. Basemap & Styling

### 2.1 Tile Provider
- **Provider**: CartoDB Dark Matter
- **URL**: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`
- **Subdomains**: `abcd`
- **Attribution**: `&copy; OpenStreetMap contributors &copy; CARTO`

### 2.2 Symbology Palette

| Entity | Color / Hex | Style |
|---|---|---|
| Trunk Highway | `#3b82f6` (Blue) | 3px Solid Line |
| Primary Highway | `#06b6d4` (Cyan) | 2.5px Solid Line |
| Secondary Highway | `#8b5cf6` (Purple) | 2px Solid Line |
| Tertiary Highway | `#64748b` (Slate) | 1.5px Solid Line |
| Strategic Corridor | `#f59e0b` (Amber) | 4px Dashed Line (`6, 8`) |
| Active Route (Fastest) | `#06b6d4` (Cyan) | 4px Solid with 8px Glow |
| Active Route (Safest) | `#10b981` (Emerald) | 4px Solid with 8px Glow |
| Active Route (Balanced)| `#a855f7` (Purple) | 4px Solid with 8px Glow |
| Alternate Route | Profile Color | 3.5px Dashed Line (`4, 6`) |
| Low Modeled Risk | `#10b981` (Green) | 6px Semi-transparent Polyline |
| Medium Modeled Risk | `#f59e0b` (Amber) | 6px Semi-transparent Polyline |
| High Modeled Risk | `#ef4444` (Red) | 6px Semi-transparent Polyline |
| Fleet Vehicle | `#10b981` / `#f59e0b` | Rounded Dark Marker (`🚚`) |
| Logistics Facility | `#6366f1` (Indigo) | Pin Marker (`📍`) |
| Consignment Delivery | `#f43f5e` (Rose) | Origin-Dest Vector & Box (`📦`) |
