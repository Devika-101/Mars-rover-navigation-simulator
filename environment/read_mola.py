import numpy as np

# MOLA file location
file_path = "data/raw/megt00n090hb.img"

# MOLA tile dimensions from the XML metadata
rows = 5632
cols = 11520

# Read the signed 16-bit elevation data
data = np.fromfile(file_path, dtype=">i2")

# Reshape into the original MOLA grid
elevation = data.reshape((rows, cols))

print("MOLA data loaded successfully!")
print("Shape:", elevation.shape)
print("Data type:", elevation.dtype)

print("\nElevation information:")
print("Minimum:", elevation.min(), "m")
print("Maximum:", elevation.max(), "m")
print("Mean:", elevation.mean(), "m")

print("\nFirst 10 elevation values:")
print(elevation.flat[:10])