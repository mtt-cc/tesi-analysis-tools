import matplotlib.pyplot as plt
import numpy as np

def load(filename):    # Load the file
    file_path = f"{filename}"
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


#------------------ LINE PLOTS ------------------

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
# plt.xlim(0, 27)
# plt.axhline(y=23, color='black', linestyle='--', label='y = 23')
plt.ylim(bottom=0)
plt.yticks(np.append(plt.yticks()[0], 23))
plt.xlabel("Time (seconds)")
plt.ylabel("Number of Nodes Discovered")
plt.title("NetworkManager Cumulative Node Discovery Time")
plt.legend()
plt.grid(True)
plt.show()


# 5% PACKET LOSS
# Generate cumulative discovery time graph
plt.figure(figsize=(10, 6))
for i, run in enumerate(netem_5_data[:10]):
    if len(run) > 0:
        cumulative_times = np.arange(1, len(run) + 1)
        plt.plot(run, cumulative_times, label=f"Run {i+1}", alpha=0.7)

plt.xlim(left=0)
plt.ylim(bottom=0)
plt.yticks(np.append(plt.yticks()[0], 23))
plt.xlabel("Time (seconds)")
plt.ylabel("Number of Nodes Discovered")
plt.title("NetworkManager Cumulative Node Discovery Time - 5% packet loss")
plt.legend()
plt.grid(True)
plt.show()

# 10% PACKET LOSS
# Generate cumulative discovery time graph
plt.figure(figsize=(10, 6))
for i, run in enumerate(netem_10_data[:10]):
    if len(run) > 0:
        cumulative_times = np.arange(1, len(run) + 1)
        plt.plot(run, cumulative_times, label=f"Run {i+1}", alpha=0.7)

plt.xlim(left=0)
plt.ylim(bottom=0)
plt.yticks(np.append(plt.yticks()[0], 23))
plt.xlabel("Time (seconds)")
plt.ylabel("Number of Nodes Discovered")
plt.title("NetworkManager Cumulative Node Discovery Time - 10% packet loss")
plt.legend()
plt.grid(True)
plt.show()

# 25% PACKET LOSS
# Generate cumulative discovery time graph
plt.figure(figsize=(10, 6))
for i, run in enumerate(netem_25_data[:10]):
    if len(run) > 0:
        cumulative_times = np.arange(1, len(run) + 1)
        plt.plot(run, cumulative_times, label=f"Run {i+1}", alpha=0.7)

plt.ylim(bottom=0)
plt.yticks(np.append(plt.yticks()[0], 23))
plt.xlabel("Time (seconds)")
plt.ylabel("Number of Nodes Discovered")
plt.title("NetworkManager Cumulative Node Discovery Time - 25% packet loss")
plt.legend()
plt.grid(True)
plt.show()

#------------------ BOX PLOTS ------------------
# Prepare data for box plot: discovery times for each node count across runs
from collections import defaultdict

nodes_discovery_time = defaultdict(list)

# Iterate over each run and collect times for each cumulative node count
for run in default_data:
    for i, time in enumerate(run):
        nodes_discovery_time[i + 1].append(time)  # Store discovery times for node count i+1
# Sort by node count (keys)
sorted_node_counts = sorted(nodes_discovery_time.keys())
boxplot_data = [nodes_discovery_time[n] for n in sorted_node_counts]
# Generate box plot
plt.figure(figsize=(12, 6))
plt.boxplot(boxplot_data, positions=sorted_node_counts, vert=False,  showfliers=True, patch_artist=True)
plt.ylabel("Number of Nodes Discovered")
plt.xlabel("Discovery Time (seconds)")
plt.title("Time Range to Discover Each Number of Nodes")
plt.grid(True)
plt.xlim(0, 27)
# Improve x-axis readability
# plt.xticks(sorted_node_counts, rotation=45)
plt.show()


nodes_discovery_time_5 = defaultdict(list)

# Iterate over each run and collect times for each cumulative node count
for run in netem_5_data:
    for i, time in enumerate(run):
        nodes_discovery_time_5[i + 1].append(time)  # Store discovery times for node count i+1
# Sort by node count (keys)
sorted_node_counts = sorted(nodes_discovery_time_5.keys())
boxplot_data = [nodes_discovery_time_5[n] for n in sorted_node_counts]
# Generate box plot
plt.figure(figsize=(12, 6))
plt.boxplot(boxplot_data, positions=sorted_node_counts, vert=False,  showfliers=True, patch_artist=True)
plt.ylabel("Number of Nodes Discovered")
plt.xlabel("Discovery Time (seconds)")
plt.title("NetworkManager - Time Range to Discover Each Number of Nodes - 5% packet loss")
plt.grid(True)
plt.xlim(0, 27)
# Improve x-axis readability
# plt.xticks(sorted_node_counts, rotation=45)
plt.show()

nodes_discovery_time_10 = defaultdict(list)

# Iterate over each run and collect times for each cumulative node count
for run in netem_10_data:
    for i, time in enumerate(run):
        nodes_discovery_time_10[i + 1].append(time)  # Store discovery times for node count i+1

# Sort by node count (keys)
sorted_node_counts = sorted(nodes_discovery_time_10.keys())
boxplot_data = [nodes_discovery_time_10[n] for n in sorted_node_counts]

# Generate box plot
plt.figure(figsize=(12, 6))
plt.boxplot(boxplot_data, positions=sorted_node_counts, vert=False, showfliers=True, patch_artist=True)
plt.ylabel("Number of Nodes Discovered")
plt.xlabel("Discovery Time (seconds)")
plt.title("NetworkManager - Time Range to Discover Each Number of Nodes - 10% packet loss")
plt.grid(True)
plt.xlim(0, 27)

# Improve x-axis readability
# plt.xticks(sorted_node_counts, rotation=45)

plt.show()

nodes_discovery_time_25 = defaultdict(list)

# Iterate over each run and collect times for each cumulative node count
for run in netem_25_data:
    for i, time in enumerate(run):
        nodes_discovery_time_25[i + 1].append(time)  # Store discovery times for node count i+1

# Sort by node count (keys)
sorted_node_counts = sorted(nodes_discovery_time_25.keys())
boxplot_data = [nodes_discovery_time_25[n] for n in sorted_node_counts]

# Generate box plot
plt.figure(figsize=(12, 6))
plt.boxplot(boxplot_data, positions=sorted_node_counts,vert=False, showfliers=True, patch_artist=True)
plt.ylabel("Number of Nodes Discovered")
plt.xlabel("Discovery Time (seconds)")
plt.title("NetworkManager - Time Range to Discover Each Number of Nodes - 25% packet loss")
plt.grid(True)
plt.xlim(0, 27)

# Improve x-axis readability
# plt.xticks(sorted_node_counts, rotation=45)

plt.show()