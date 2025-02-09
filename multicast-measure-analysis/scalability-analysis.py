import matplotlib.pyplot as plt
import numpy as np

def load(filename):    # Load the file
    file_path = "../multicast-measures/results/netmanager-scalability.txt"
    with open(file_path, "r") as file:
        lines = file.readlines()

    # Process the data
    all_runs = []
    current_run = []

    for line in lines:
        line = line.strip()
        if line == "----------------":
            if current_run:
                all_runs.append(sorted(current_run))  # Sort each run by discovery time
                current_run = []
        else:
            parts = line.split()
            try:
                time = float(parts[0])  # Convert first part to float
                current_run.append(time)
            except ValueError:
                continue  # Ignore lines that do not start with a number

    # Append the last run if it exists
    if current_run:
        all_runs.append(sorted(current_run))

    # Check if data exists
    if not all_runs:
        raise ValueError("No valid discovery time data found.")
    return all_runs


# DEFAULT

default_data = load("../multicast-measures/results/netmanager-scalability.txt")
netem_5_data = load("../multicast-measures/results/netmanager-scalability-netem-5.txt")
netem_10_data = load("../multicast-measures/results/netmanager-scalability-netem-10.txt")
netem_25_data = load("../multicast-measures/results/netmanager-scalability-netem-25.txt")

# Generate cumulative discovery time graph
plt.figure(figsize=(10, 6))

for i, run in enumerate(default_data):
    if len(run) > 0:
        cumulative_times = np.arange(1, len(run) + 1)
        plt.plot(run, cumulative_times, label=f"Run {i+1}", alpha=0.7)

plt.xlabel("Time (seconds)")
plt.ylabel("Cumulative Nodes Discovered")
plt.title("NetworkManager Cumulative Node Discovery Time")
plt.legend()
plt.grid(True)
plt.show()

# Generate cumulative discovery time graph
plt.figure(figsize=(10, 6))

for i, run in enumerate(default_data):
    if len(run) > 0:
        cumulative_times = np.arange(1, len(run) + 1)
        plt.plot(run, cumulative_times, label=f"Run {i+1}", alpha=0.7)

plt.xlabel("Time (seconds)")
plt.ylabel("Cumulative Nodes Discovered")
plt.title("NetworkManager Cumulative Node Discovery Time")
plt.legend()
plt.grid(True)
plt.show()
