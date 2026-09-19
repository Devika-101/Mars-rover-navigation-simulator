import numpy as np
import matplotlib.pyplot as plt

# --------------------------------------------------
# Load Gale Crater navigation grid
# --------------------------------------------------
elevation = np.load("data/navigation_grid.npy")

print("Grid shape:", elevation.shape)

# --------------------------------------------------
# Physical dimensions of the navigation grid
# --------------------------------------------------

# Gale Crater region covers approximately 4° x 4°
region_degrees = 4.0

# Mars radius in kilometres
mars_radius = 3389.5

# Approximate latitude of Gale Crater
gale_latitude = -5.4

# Convert degrees to kilometres
km_per_degree_lat = np.pi * mars_radius / 180

km_per_degree_lon = (
    np.pi * mars_radius / 180
    * np.cos(np.radians(gale_latitude))
)

# 100 grid cells are represented by 99 intervals
grid_intervals = elevation.shape[0] - 1

# Physical distance between neighbouring grid points
dy = (region_degrees / grid_intervals) * km_per_degree_lat * 1000
dx = (region_degrees / grid_intervals) * km_per_degree_lon * 1000

print("\nGrid spacing:")
print("North-South:", round(dy / 1000, 3), "km")
print("East-West:", round(dx / 1000, 3), "km")

# --------------------------------------------------
# Calculate elevation gradient
# --------------------------------------------------

# np.gradient calculates dz/dy and dz/dx
gy, gx = np.gradient(elevation, dy, dx)

# --------------------------------------------------
# Calculate slope angle
# --------------------------------------------------

# Gradient magnitude
slope_gradient = np.sqrt(gx**2 + gy**2)

# Convert gradient to slope angle
slope_angle = np.degrees(np.arctan(slope_gradient))

# --------------------------------------------------
# Create terrain movement cost
# --------------------------------------------------

# Maximum slope considered traversable
MAX_TRAVERSABLE_SLOPE = 25.0

# Normalize slope between 0 and the maximum
slope_normalized = np.clip(
    slope_angle / MAX_TRAVERSABLE_SLOPE,
    0,
    1
)

# Convert slope into movement cost
# 1 = easiest terrain
# 10 = most difficult traversable terrain
cost_map = 1 + 9 * slope_normalized

print("\nTerrain classification:")

print("Easy terrain (< 5°):",
      np.sum(slope_angle < 5))

print("Moderate terrain (5°–15°):",
      np.sum((slope_angle >= 5) & (slope_angle < 15)))

print("Difficult terrain (15°–25°):",
      np.sum((slope_angle >= 15) & (slope_angle <= 25)))

print("Obstacle terrain (> 25°):",
      np.sum(slope_angle > 25))
# --------------------------------------------------
# Identify unsafe terrain
# --------------------------------------------------

obstacles = slope_angle > MAX_TRAVERSABLE_SLOPE

print("\nTerrain cost information:")
print("Minimum cost:", round(cost_map.min(), 2))
print("Maximum cost:", round(cost_map.max(), 2))
print("Obstacle cells:", np.sum(obstacles))

# --------------------------------------------------
# Visualize movement cost
# --------------------------------------------------

plt.figure(figsize=(8, 6))

plt.imshow(cost_map, cmap="inferno")

plt.colorbar(label="Movement Cost")

plt.title("Mars Rover Terrain Movement Cost")

plt.xlabel("X")
plt.ylabel("Y")

plt.show()

# --------------------------------------------------
# Visualize obstacles
# --------------------------------------------------

plt.figure(figsize=(8, 6))

plt.imshow(obstacles, cmap="gray")

plt.colorbar(label="Obstacle")

plt.title("Unsafe Terrain Regions")

plt.xlabel("X")
plt.ylabel("Y")

plt.show()

print("\nSlope information:")
print("Minimum slope:", round(slope_angle.min(), 2), "degrees")
print("Maximum slope:", round(slope_angle.max(), 2), "degrees")
print("Mean slope:", round(slope_angle.mean(), 2), "degrees")

# --------------------------------------------------
# Visualize elevation
# --------------------------------------------------

plt.figure(figsize=(8, 6))

plt.imshow(elevation, cmap="terrain")

plt.colorbar(label="Elevation (m)")

plt.title("Gale Crater Elevation Map")

plt.xlabel("X")
plt.ylabel("Y")

plt.show()

# --------------------------------------------------
# Visualize slope
# --------------------------------------------------

plt.figure(figsize=(8, 6))

plt.imshow(slope_angle, cmap="terrain")

plt.colorbar(label="Slope Angle (degrees)")

plt.title("Gale Crater Terrain Slope")

plt.xlabel("X")
plt.ylabel("Y")

plt.show()

# --------------------------------------------------
# Save terrain information
# --------------------------------------------------

np.save("data/slope_angle.npy", slope_angle)
np.save("data/cost_map.npy", cost_map)
np.save("data/obstacles.npy", obstacles)

print("\nSaved:")
print("data/slope_angle.npy")
print("data/cost_map.npy")
print("data/obstacles.npy")