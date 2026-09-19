import heapq
import numpy as np


def get_neighbors(row, col, rows, cols):
    """
    Return the four neighboring cells:
    up, down, left, right.
    """

    directions = [
        (-1, 0),  # up
        (1, 0),   # down
        (0, -1),  # left
        (0, 1)    # right
    ]

    neighbors = []

    for dr, dc in directions:
        new_row = row + dr
        new_col = col + dc

        if 0 <= new_row < rows and 0 <= new_col < cols:
            neighbors.append((new_row, new_col))

    return neighbors


def reconstruct_path(previous, start, goal):
    """
    Reconstruct the shortest path from start to goal.
    """

    path = []
    current = goal

    while current is not None:
        path.append(current)

        if current == start:
            break

        current = previous[current]

    # Goal was not reachable
    if path[-1] != start:
        return None

    path.reverse()
    return path


def dijkstra(cost_map, obstacles, start, goal):
    """
    Find the minimum-cost path using Dijkstra's algorithm.

    Parameters:
        cost_map : 2D numpy array
            Movement cost of each cell.

        obstacles : 2D numpy array of bool
            True means the cell is blocked.

        start : tuple
            Starting position as (row, column).

        goal : tuple
            Goal position as (row, column).

    Returns:
        path : list of tuples
            Shortest path from start to goal.

        total_cost : float
            Total movement cost of the path.
    """

    rows, cols = cost_map.shape

    # Check that start and goal are inside the grid
    if not (0 <= start[0] < rows and 0 <= start[1] < cols):
        raise ValueError("Start position is outside the grid.")

    if not (0 <= goal[0] < rows and 0 <= goal[1] < cols):
        raise ValueError("Goal position is outside the grid.")

    # Start or goal cannot be an obstacle
    if obstacles[start]:
        raise ValueError("Start position is an obstacle.")

    if obstacles[goal]:
        raise ValueError("Goal position is an obstacle.")

    # Distance from start to every cell
    distances = np.full((rows, cols), np.inf)

    # Previous cell used to reach each cell
    previous = np.full((rows, cols), None, dtype=object)

    # Start has zero cost
    distances[start] = 0.0

    # Priority queue: (cost, row, column)
    priority_queue = [(0.0, start[0], start[1])]

    while priority_queue:

        current_cost, row, col = heapq.heappop(priority_queue)

        current = (row, col)

        # Ignore outdated queue entries
        if current_cost > distances[current]:
            continue

        # Goal reached
        if current == goal:
            break

        # Check neighboring cells
        for neighbor in get_neighbors(row, col, rows, cols):

            nr, nc = neighbor

            # Skip obstacles
            if obstacles[nr, nc]:
                continue

            # Movement cost of entering the neighboring cell
            movement_cost = cost_map[nr, nc]

            new_cost = current_cost + movement_cost

            # Found a cheaper path
            if new_cost < distances[nr, nc]:

                distances[nr, nc] = new_cost
                previous[nr, nc] = current

                heapq.heappush(
                    priority_queue,
                    (new_cost, nr, nc)
                )

    # Goal cannot be reached
    if np.isinf(distances[goal]):
        return None, np.inf

    # Reconstruct path
    path = reconstruct_path(previous, start, goal)

    return path, distances[goal]


if __name__ == "__main__":

    # Load the data created by the environment
    cost_map = np.load("data/cost_map.npy")
    obstacles = np.load("data/obstacles.npy")

    # Example start and goal
    start = (0, 0)
    goal = (99, 99)

    path, total_cost = dijkstra(
        cost_map,
        obstacles,
        start,
        goal
    )

    if path is None:
        print("No path found.")
    else:
        print("Path found!")
        print("Number of cells:", len(path))
        print("Total cost:", total_cost)
        print("Start:", start)
        print("Goal:", goal)
