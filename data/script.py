import csv
import random

random.seed(42)

SIZE = 100

# ==========================
# TERRAIN GENERATION
# ==========================

height_matrix = []
type_matrix = []

for y in range(SIZE):

    height_row = []
    type_row = []

    for x in range(SIZE):

        h = random.randint(0, 75)

        if h <= 2:
            t = 5      # Water
        elif h <= 10:
            t = 4      # Valley
        elif h <= 25:
            t = 0      # Plain
        elif h <= 45:
            t = 2      # Hill
        else:
            t = 3      # Mountain

        if t in [0, 2] and random.random() < 0.15:
            t = 1      # Forest

        height_row.append(h)
        type_row.append(t)

    height_matrix.append(height_row)
    type_matrix.append(type_row)

with open("terrain_height.csv", "w", newline="") as f:
    csv.writer(f).writerows(height_matrix)

with open("terrain_type.csv", "w", newline="") as f:
    csv.writer(f).writerows(type_matrix)

# ==========================
# SENSOR GENERATION
# ==========================

sensors = []

sensor_types = [
    ("Radar", 8),
    ("IR", 8),
    ("Acoustic", 8),
    ("Visual", 8)
]

sensor_id = 1

for sensor_type, count in sensor_types:

    for i in range(count):

        x = random.randint(0, 99)
        y = random.randint(0, 99)
        z = random.randint(0, 100)

        terrain_class = type_matrix[y][x]

        sensors.append([
            sensor_id,
            sensor_type,
            f"{sensor_type}_{i+1}",
            x,
            y,
            z,
            terrain_class
        ])

        sensor_id += 1

with open("sensor.csv", "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "id",
        "sensor_type",
        "label",
        "x",
        "y",
        "z",
        "class"
    ])

    writer.writerows(sensors)

print("Generated:")
print(" - terrain_height.csv")
print(" - terrain_type.csv")
print(" - sensor.csv")