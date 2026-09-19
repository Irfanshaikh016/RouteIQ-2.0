# RouteIQ 2.0 — CVRP & VRP-TW Optimization Solvers (Phase 6)

## 1. Capacitated Vehicle Routing Problem (CVRP)

### Mathematical Formulation
Given:
- A depot node $0$ and a set of delivery customer nodes $V_c = \{1, \dots, n\}$.
- A fleet of vehicles $K = \{1, \dots, m\}$ with individual capacities $Q_k$.
- Delivery demands $d_i$ for each customer stop $i \in V_c$.
- Travel cost $c_{ij}$ between any two nodes.

The objective is to minimize total system routing cost:
$$\min \sum_{k \in K} \sum_{i \in V} \sum_{j \in V} c_{ij} x_{ijk}$$
Subject to:
1. Every customer stop is visited exactly once:
   $$\sum_{k \in K} \sum_{j \in V, j \neq i} x_{ijk} = 1 \quad \forall i \in V_c$$
2. Every vehicle starts and ends its route at the central depot:
   $$\sum_{j \in V_c} x_{0jk} \le 1, \quad \sum_{i \in V_c} x_{i0k} \le 1 \quad \forall k \in K$$
3. Vehicle capacity is never exceeded along any route:
   $$\sum_{i \in V_c} d_i \sum_{j \in V} x_{ijk} \le Q_k \quad \forall k \in K$$

### OR-Tools Implementation
Configured using `routing.AddDimensionWithVehicleCapacity()` with `RegisterUnaryTransitCallback`:
```python
def demand_callback(from_index: int) -> int:
    from_node = manager.IndexToNode(from_index)
    return demands[from_node]
```

---

## 2. Vehicle Routing Problem with Time Windows (VRP-TW)

### Temporal Formulation
Extends CVRP by associating each delivery stop $i$ with:
- Earliest arrival time $a_i$ (window start)
- Latest deadline $b_i$ (window end)
- Unloading / service dwell duration $s_i$

Arrival time $T_j$ at consecutive node $j$ satisfies:
$$T_j \ge T_i + s_i + t_{ij} \quad \text{if } x_{ijk} = 1$$
$$a_i \le T_i \le b_i \quad \forall i \in V_c$$

If a vehicle arrives before $a_i$, it incurs waiting time $W_i = a_i - (T_{\text{prev}} + s_{\text{prev}} + t_{\text{prev}, i})$.

### OR-Tools Implementation
Configured using `routing.AddDimension()` with `RegisterTransitCallback`:
```python
def time_callback(from_index: int, to_index: int) -> int:
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return duration_matrix[from_node][to_node] + service_durations[from_node]
```

---

## 3. Infeasibility Diagnostic Engine

Instead of returning opaque solver failure codes when constraints cannot be satisfied, RouteIQ 2.0 provides actionable diagnostics:

| Condition | Diagnostic Code | Actionable Guidance |
|---|---|---|
| Single delivery demand > largest vehicle capacity | `DELIVERY_EXCEEDS_MAX_CAPACITY` | Explains delivery ID, demand weight, and maximum vehicle capacity. Suggests vehicle upgrade. |
| Total demand across orders > sum of fleet capacities | `INSUFFICIENT_CAPACITY` | Quantifies shortfall in fleet capacity. Suggests adding vehicles. |
| Delivery deadline < travel time from depot | `NO_FEASIBLE_TIME_WINDOW` | Indicates physical reachability impossibility given road speeds. |
| Start time > End time for a customer window | `INVALID_TIME_WINDOW` | Identifies invalid input chronology. |

---

## 4. Multi-Profile Neutral Comparison

The `/api/v1/optimization/compare` endpoint solves CVRP or VRP-TW across all three cost models (`fastest`, `safest`, `balanced`):
- Results are presented side-by-side with objective distance, travel duration, composite risk, and capacity utilization.
- Adheres strictly to the **zero ranking/winner bias guarantee**: operators are presented neutral trade-off metrics to exercise professional dispatch judgment.
