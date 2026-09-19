import numpy as np

# -----------------------------
# MOLA file information
# -----------------------------
file_path = "data/raw/megt00n090hb.img"

rows = 5632
cols = 11520

# MOLA coverage
west = 90.0
east = 180.0
north = 0.0
south = -44.0

pixels_per_degree = 128

# -----------------------------
# Gale Crater approximate center
# -----------------------------
gale_lon = 137.4
gale_lat = -5.4

# Region around Gale
lon_range = 2.0
lat_range = 2.0

# -----------------------------
# Read MOLA data
# -----------------------------
data = np.fromfile(file_path, dtype=">i2")
elevation = data.reshape((rows, cols))

# -----------------------------
# Convert coordinates to pixels
# -----------------------------
col_start = int((gale_lon - lon_range - west) * pixels_per_degree)
col_end = int((gale_lon + lon_range - west) * pixels_per_degree)

row_start = int((north - (gale_lat + lat_range)) * pixels_per_degree)
row_end = int((north - (gale_lat - lat_range)) * pixels_per_degree)

# Extract region
gale_region = elevation[row_start:row_end, col_start:col_end]

print("Gale region extracted successfully!")

print("Region shape:", gale_region.shape)

print("\nElevation information:")
print("Minimum:", gale_region.min(), "m")
print("Maximum:", gale_region.max(), "m")
print("Mean:", gale_region.mean(), "m")

print("\nPixel boundaries:")
print("Rows:", row_start, "to", row_end)
print("Columns:", col_start, "to", col_end)
import matplotlib.pyplot as plt

# Display the extracted elevation map
plt.figure(figsize=(8, 6))
plt.imshow(gale_region, cmap="terrain")
plt.colorbar(label="Elevation (m)")
plt.title("MOLA Elevation Map - Gale Crater Region")
plt.xlabel("Longitude direction")
plt.ylabel("Latitude direction")
plt.show()
# Save extracted Gale region
np.save("data/gale_elevation.npy", gale_region)

print("\nSaved Gale elevation data to:")
print("data/gale_elevation.npy")
# Save extracted Gale region
np.save("data/gale_elevation.npy", gale_region)

print("\nSaved Gale elevation data to:")
print("data/gale_elevation.npy")