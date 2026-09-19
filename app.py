from flask import Flask, jsonify, request, render_template
import numpy as np
import time
import heapq
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

app = Flask(__name__, template_folder="ui", static_folder="static")

def load_environment():
    elevation = np.load(DATA / "navigation_grid.npy")
    slope = np.load(DATA / "slope_angle.npy")
    cost = np.load(DATA / "cost_map.npy")
    obstacles = np.load(DATA / "obstacles.npy")
    return elevation, slope, cost, obstacles

def neighbors(r, c, rows, cols):
    for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            yield nr, nc

def dijkstra(cost, obstacles, start, goal, extra_obstacles=None):
    blocked = obstacles.copy()
    if extra_obstacles:
        for r, c in extra_obstacles:
            if 0 <= r < blocked.shape[0] and 0 <= c < blocked.shape[1]:
                blocked[r, c] = True
    if blocked[start] or blocked[goal]:
        return None, float("inf"), 0

    dist = np.full(cost.shape, np.inf)
    prev = np.full(cost.shape, None, dtype=object)
    dist[start] = 0.0
    pq = [(0.0, start[0], start[1])]
    explored = 0

    while pq:
        d, r, c = heapq.heappop(pq)
        if d != dist[r, c]:
            continue
        explored += 1
        if (r, c) == goal:
            break
        for nr, nc in neighbors(r, c, *cost.shape):
            if blocked[nr, nc]:
                continue
            nd = d + float(cost[nr, nc])
            if nd < dist[nr, nc]:
                dist[nr, nc] = nd
                prev[nr, nc] = (r, c)
                heapq.heappush(pq, (nd, nr, nc))

    if np.isinf(dist[goal]):
        return None, float("inf"), explored

    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        if cur == start:
            break
        cur = prev[cur]
    path.reverse()
    return path, float(dist[goal]), explored

def astar(cost, obstacles, start, goal, extra_obstacles=None):
    """Temporary self-contained A* adapter.
    Replace/import the teammate's A* implementation when it is merged."""
    blocked = obstacles.copy()
    if extra_obstacles:
        for r, c in extra_obstacles:
            if 0 <= r < blocked.shape[0] and 0 <= c < blocked.shape[1]:
                blocked[r, c] = True
    if blocked[start] or blocked[goal]:
        return None, float("inf"), 0

    rows, cols = cost.shape
    g = np.full(cost.shape, np.inf)
    prev = np.full(cost.shape, None, dtype=object)
    g[start] = 0.0
    # Manhattan distance is admissible when the minimum cell cost is >= 1.
    min_cost = max(1.0, float(cost[~blocked].min()))
    def h(p):
        return (abs(p[0]-goal[0]) + abs(p[1]-goal[1])) * min_cost

    pq = [(h(start), 0.0, start[0], start[1])]
    explored = 0
    while pq:
        f, d, r, c = heapq.heappop(pq)
        if d != g[r, c]:
            continue
        explored += 1
        if (r, c) == goal:
            break
        for nr, nc in neighbors(r, c, rows, cols):
            if blocked[nr, nc]:
                continue
            nd = d + float(cost[nr, nc])
            if nd < g[nr, nc]:
                g[nr, nc] = nd
                prev[nr, nc] = (r, c)
                heapq.heappush(pq, (nd + h((nr, nc)), nd, nr, nc))

    if np.isinf(g[goal]):
        return None, float("inf"), explored

    path, cur = [], goal
    while cur is not None:
        path.append(cur)
        if cur == start:
            break
        cur = prev[cur]
    path.reverse()
    return path, float(g[goal]), explored

def run_algorithm(name, cost, obstacles, start, goal, extra_obstacles=None):
    t0 = time.perf_counter()
    if name == "dijkstra":
        path, total, explored = dijkstra(cost, obstacles, start, goal, extra_obstacles)
    else:
        path, total, explored = astar(cost, obstacles, start, goal, extra_obstacles)
    elapsed = (time.perf_counter() - t0) * 1000
    return {
        "path": path,
        "cost": None if path is None else total,
        "cells": 0 if path is None else len(path),
        "explored": explored,
        "time_ms": elapsed,
        "reachable": path is not None
    }

def battery_cost(path, slope):
    """Sum the same per-step battery drain used by the frontend simulation
    (see consumeBattery() in app.js), so the feasibility check here actually
    predicts what the run will consume."""
    if not path:
        return 0.0
    total = 0.0
    for r, c in path[1:]:
        s = float(slope[r, c])
        total += 0.012 + 0.003 * min(s, 25)
    return total

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/environment")
def environment():
    elevation, slope, cost, obstacles = load_environment()
    return jsonify({
        "rows": int(elevation.shape[0]),
        "cols": int(elevation.shape[1]),
        "elevation": elevation.round(2).tolist(),
        "slope": slope.round(2).tolist(),
        "cost": cost.round(3).tolist(),
        "obstacles": obstacles.astype(int).tolist(),
        "stats": {
            "min_elevation": float(elevation.min()),
            "max_elevation": float(elevation.max()),
            "mean_elevation": float(elevation.mean()),
            "min_slope": float(slope.min()),
            "max_slope": float(slope.max()),
            "mean_slope": float(slope.mean()),
            "obstacle_cells": int(obstacles.sum())
        }
    })

@app.post("/api/plan")
def plan():
    body = request.get_json(force=True)
    start = tuple(map(int, body.get("start", [0, 0])))
    goal = tuple(map(int, body.get("goal", [99, 99])))
    battery = float(body.get("battery", 100))
    algorithm = body.get("algorithm", "astar").lower()
    dynamic = [tuple(map(int, p)) for p in body.get("dynamic_obstacles", [])]

    elevation, slope, cost, obstacles = load_environment()
    rows, cols = cost.shape
    for p in (start, goal):
        if not (0 <= p[0] < rows and 0 <= p[1] < cols):
            return jsonify({"error": "Start or goal is outside the grid."}), 400

    outward = run_algorithm(algorithm, cost, obstacles, start, goal, dynamic)
    if not outward["reachable"]:
        return jsonify({"reachable": False, "message": "No path exists to the selected target."})

    # Return path is planned against the same current environment.
    home = run_algorithm(algorithm, cost, obstacles, goal, start, dynamic)
    if not home["reachable"]:
        return jsonify({"reachable": False, "message": "Target is reachable, but a return path to base is not available."})

    round_trip_cost = outward["cost"] + home["cost"]

    # Battery model: mirror the exact per-step drain the frontend simulation
    # applies during the run (0.012 base drain + slope-scaled drain per cell),
    # rather than a rough terrain-cost estimate. This keeps the feasibility
    # check consistent with what will actually happen when the rover runs.
    battery_needed = battery_cost(outward["path"], slope) + battery_cost(home["path"], slope)
    possible = battery >= battery_needed

    return jsonify({
        "reachable": True,
        "mission_possible": possible,
        "message": "Mission and return are feasible." if possible else "Insufficient battery for the planned round trip.",
        "algorithm": algorithm,
        "outward": outward,
        "return": home,
        "round_trip_cost": round_trip_cost,
        "estimated_battery_needed": battery_needed,
        "battery_start": battery,
        "dynamic_obstacles": [list(p) for p in dynamic]
    })

@app.post("/api/replan")
def replan():
    """Recalculate a single leg (e.g. rover's current position -> its current
    destination) after a new dynamic hazard appears mid-mission. Unlike
    /api/plan, this does not run the round-trip battery feasibility check —
    it's a live reroute around an obstacle, not a fresh mission plan."""
    body = request.get_json(force=True)
    start = tuple(map(int, body.get("start", [0, 0])))
    goal = tuple(map(int, body.get("goal", [99, 99])))
    algorithm = body.get("algorithm", "astar").lower()
    dynamic = [tuple(map(int, p)) for p in body.get("dynamic_obstacles", [])]

    _, _, cost, obstacles = load_environment()
    rows, cols = cost.shape
    for p in (start, goal):
        if not (0 <= p[0] < rows and 0 <= p[1] < cols):
            return jsonify({"error": "Start or goal is outside the grid."}), 400

    result = run_algorithm(algorithm, cost, obstacles, start, goal, dynamic)
    return jsonify(result)

@app.post("/api/reroute")
def reroute():
    """Recompute a single-leg path from an arbitrary start (typically the
    rover's current position) to a goal, avoiding the given hazards.
    Used when a dynamic hazard is placed on a route already in progress."""
    body = request.get_json(force=True)
    start = tuple(map(int, body.get("start", [0, 0])))
    goal = tuple(map(int, body.get("goal", [99, 99])))
    algorithm = body.get("algorithm", "astar").lower()
    dynamic = [tuple(map(int, p)) for p in body.get("dynamic_obstacles", [])]

    _, _, cost, obstacles = load_environment()
    rows, cols = cost.shape
    for p in (start, goal):
        if not (0 <= p[0] < rows and 0 <= p[1] < cols):
            return jsonify({"error": "Start or goal is outside the grid."}), 400

    result = run_algorithm(algorithm, cost, obstacles, start, goal, dynamic)
    return jsonify(result)

@app.post("/api/compare")
def compare():
    body = request.get_json(force=True)
    start = tuple(map(int, body.get("start", [0, 0])))
    goal = tuple(map(int, body.get("goal", [99, 99])))
    dynamic = [tuple(map(int, p)) for p in body.get("dynamic_obstacles", [])]
    _, _, cost, obstacles = load_environment()

    a = run_algorithm("astar", cost, obstacles, start, goal, dynamic)
    d = run_algorithm("dijkstra", cost, obstacles, start, goal, dynamic)
    return jsonify({
        "start": list(start), "goal": list(goal),
        "astar": a, "dijkstra": d
    })

if __name__ == "__main__":
    app.run(debug=True)