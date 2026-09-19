import heapq
import numpy as np


# Load the provided Gale Crater data
GRID = np.load("data/navigation_grid.npy")
COST_MAP = np.load("data/cost_map.npy")
OBSTACLES = np.load("data/obstacles.npy")


def heuristic(a, b):
    """
    Manhattan distance heuristic.
    a and b are (row, column) coordinates.
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def get_neighbors(node):
    """
    Return valid 4-directional neighbors.
    """
    row, col = node

    directions = [
        (-1, 0),  # up
        (1, 0),   # down
        (0, -1),  # left
        (0, 1)    # right
    ]

    neighbors = []

    for dr, dc in directions:
        nr = row + dr
        nc = col + dc

        # Check grid boundaries
        if 0 <= nr < GRID.shape[0] and 0 <= nc < GRID.shape[1]:

            # Skip obstacle cells
            if not OBSTACLES[nr, nc]:
                neighbors.append((nr, nc))

    return neighbors


def reconstruct_path(came_from, current):
    """
    Reconstruct path from goal back to start.
    """
    path = [current]

    while current in came_from:
        current = came_from[current]
        path.append(current)

    path.reverse()
    return path


def astar(start, goal):
    """
    Find the lowest-cost path from start to goal using A*.

    Returns:
        path       : list of (row, column)
        total_cost : total movement cost
    """

    # Check start and goal
    if OBSTACLES[start]:
        raise ValueError("Start position is an obstacle.")

    if OBSTACLES[goal]:
        raise ValueError("Goal position is an obstacle.")

    # Priority queue:
    # (f_score, node)
    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}

    # Cost from start to each node
    g_score = {
        start: 0.0
    }

    while open_set:

        _, current = heapq.heappop(open_set)

        # Goal reached
        if current == goal:
            path = reconstruct_path(came_from, current)
            return path, g_score[current]

        for neighbor in get_neighbors(current):

            # Cost of entering this cell
            movement_cost = COST_MAP[neighbor]

            tentative_g = g_score[current] + movement_cost

            # If this path is better
            if (
                neighbor not in g_score
                or tentative_g < g_score[neighbor]
            ):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g

                f_score = (
                    tentative_g
                    + heuristic(neighbor, goal)
                )

                heapq.heappush(
                    open_set,
                    (f_score, neighbor)
                )

    # No path found
    return None, float("inf")


if __name__ == "__main__":

    # Example start and goal
    start = (0, 0)
    goal = (99, 99)

    path, total_cost = astar(start, goal)

    if path is not None:
        print("A* Path Found!")
        print("Start:", start)
        print("Goal:", goal)
        print("Number of cells:", len(path))
        print("Total path cost:", total_cost)

        print("\nFirst 10 path cells:")
        print(path[:10])

        print("\nLast 10 path cells:")
        print(path[-10:])

    else:
        print("No path found.")