import numpy as np
import matplotlib.pyplot as plt

# Load Gale Crater navigation grid
elevation = np.load("data/navigation_grid.npy")

print("Grid shape:", elevation.shape)

# Calculate elevation gradient
gy, gx = np.gradient(elevation)

# Approximate slope magnitude
slope = np.sqrt(gx**2 + gy**2)

# Normalize slope
slope_normalized = (slope - slope.min()) / (slope.max() - slope.min())

# Create terrain cost
# Flat terrain = lower cost
# Steep terrain = higher cost
cost_map = 1 + 9 * slope_normalized

# Mark extremely steep regions as obstacles
OBSTACLE_THRESHOLD = 7

obstacles = cost_map > OBSTACLE_THRESHOLD

print("Terrain processing completed!")
print("Minimum cost:", cost_map.min())
print("Maximum cost:", cost_map.max())
print("Obstacle cells:", np.sum(obstacles))

# Save for algorithms
np.save("data/cost_map.npy", cost_map)
np.save("data/obstacles.npy", obstacles)

# Visualize
plt.figure(figsize=(8, 6))
plt.imshow(elevation, cmap="terrain")
plt.colorbar(label="Elevation (m)")
plt.title("Gale Crater Elevation Map")
plt.xlabel("X")
plt.ylabel("Y")
plt.show()

plt.figure(figsize=(8, 6))
plt.imshow(cost_map, cmap="inferno")
plt.colorbar(label="Movement Cost")
plt.title("Mars Rover Navigation Cost Map")
plt.xlabel("X")
plt.ylabel("Y")
plt.show()