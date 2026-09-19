import numpy as np

# Load Gale Crater elevation data
elevation = np.load("data/gale_elevation.npy")

print("Original elevation shape:", elevation.shape)

# Navigation grid size
grid_size = 100

# Calculate sampling intervals
row_indices = np.linspace(
    0,
    elevation.shape[0] - 1,
    grid_size
).astype(int)

col_indices = np.linspace(
    0,
    elevation.shape[1] - 1,
    grid_size
).astype(int)

# Create 100 x 100 navigation grid
navigation_grid = elevation[np.ix_(row_indices, col_indices)]

print("Navigation grid created!")
print("Grid shape:", navigation_grid.shape)

print("\nElevation information:")
print("Minimum:", navigation_grid.min(), "m")
print("Maximum:", navigation_grid.max(), "m")
print("Mean:", navigation_grid.mean(), "m")

# Save grid
np.save("data/navigation_grid.npy", navigation_grid)

print("\nSaved to:")
print("data/navigation_grid.npy")