# create_artifacts.py
# This script runs as a Domino job and writes a file to /mnt/create_artifacts

import os

artifacts_dir = "/mnt/artifacts"
file_path = os.path.join(artifacts_dir, "outout.txt")

os.makedirs(artifacts_dir, exist_ok=True)

with open(file_path, "w") as f:
    f.write("Hello from artifacts!\n")

print(f"File successfully written to {file_path}")