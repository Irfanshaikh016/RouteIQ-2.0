# RouteIQ 2.0 — Dispatch Operations Console Guide (Phase 6)

## 1. Overview

The Operations Console (`/dashboard`) integrates real-time GIS cartography with combinatorial fleet dispatch controls in a single unified interface.

## 2. Dispatch Tab Workflow

### Step 1: Select Central Depot & Constraints
1. Switch to the **🚚 Dispatch** tab on the left console panel.
2. Select your origin facility (or accept the default Guwahati hub).
3. Toggle between **CVRP (Payload Capacity)** and **VRP-TW (Capacity + Customer Time Windows)**.
4. Select your multi-objective profile:
   - ⚡ **Fastest**: Prioritizes minimum travel duration.
   - ⚖️ **Balanced**: Equal consideration of time, distance, terrain, and risk.
   - 🛡️ **Safest**: Maximum avoidance of landslide/flood corridors and steep gradients.

### Step 2: Select Fleet Vehicles & Orders
- Check/uncheck vehicles in the **Available Fleet Vehicles** list. Each card displays registration number and payload capacity in kg.
- Check/uncheck orders in the **Pending Orders** list. Each card displays consignment reference number, destination, and package weight.

### Step 3: Run Optimization
- Click **🚀 Run Fleet Optimization**.
- OR-Tools executes the combinatorial solver.
- The solution displays:
  - Total vehicles deployed vs available.
  - Deliveries served count.
  - Cumulative distance and duration.
  - Per-vehicle payload utilization bar graph ($0\% \dots 100\%$).
  - Chronological stop-by-stop schedule with arrival, waiting, dwell, and departure timestamps.

### Step 4: Map Visualization
- Each deployed vehicle is drawn in its distinct color:
  - Route 1: `#06b6d4` (Cyan)
  - Route 2: `#a855f7` (Purple)
  - Route 3: `#10b981` (Emerald)
  - Route 4: `#f59e0b` (Amber)
- Stops are numbered sequentially along the route with sequence badges.
- Live telemetry vehicles pulse with freshness halo rings (`LIVE` green, `STALE` amber, `OFFLINE` gray).
- Road closures are overlaid as red dashed corridors.

### Step 5: Test Operational Disruptions
- Click **💥 Breakdown**, **🚧 Road Closed**, or **❌ Cancel Order** in the disruption bar to test the debounced dynamic re-optimization engine.
