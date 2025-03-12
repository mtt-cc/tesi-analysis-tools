import matplotlib.pyplot as plt
import numpy as np

def setup_publication_style():
    """Configure consistent styling for all plots."""
    # Define color scheme
    colors = {
        'primary': '#1f77b4',      # Default blue for main data
        'secondary': '#ff7f0e',    # Orange for comparisons
        'tertiary': '#2ca02c',     # Green for third series
        'highlight': '#d62728'     # Red for highlights
    }
    
    # Set consistent styling
    plt.rcParams.update({
        'font.family': 'serif',
        'font.size': 11,
        'axes.titlesize': 14,
        'axes.labelsize': 12
    })
        
    return colors

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

def save_publication_figure(filename, title=None, dpi=600):
    """Save the current figure with publication-quality settings.
    
    Args:
        filename: Name of output file (without extension)
        title: Optional title to display on graph
        dpi: Resolution for raster elements (default: 600)
    """
    # Create figures directory if it doesn't exist
    output_dir = 'figures'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Set title if provided
    if title:
        plt.title(title)
    
    # Save figure with publication settings
    filepath = os.path.join(output_dir, f"{filename}.pdf")
    plt.savefig(filepath, 
                format='pdf', 
                dpi=dpi, 
                bbox_inches='tight')  # Trim whitespace
    print(f"Figure saved to {filepath}")


#------------------ LINE PLOTS ------------------

setup_publication_style()

default_data = load("../multicast-measures/results/netmanager-scalability.txt")
network_manager_netem_5_data = load("../multicast-measures/results/netmanager-scalability-netem-5.txt")
network_manager_netem_10_data = load("../multicast-measures/results/netmanager-scalability-netem-10.txt")
network_manager_netem_25_data = load("../multicast-measures/results/netmanager-scalability-netem-25.txt")
neuropil_default_data = load("../multicast-measures/results/neuropil-scalability.txt")
neuropil_default_data_2 = load("../multicast-measures/results/neuropil-scalability-2.txt")
neuropil_netem_10_data = load("../multicast-measures/results/neuropil-scalability-netem-10.txt")

# Generate cumulative discovery time graph
plt.figure(figsize=(10, 6))

for i, run in enumerate(default_data[:10]):
    if len(run) > 0:
        cumulative_times = np.arange(1, len(run) + 1)
        plt.plot(run, cumulative_times, label=f"Run {i+1}", alpha=0.7)

plt.xlim(left=0)
plt.ylim(bottom=1)
plt.yticks([1, 5, 10, 15, 20, 23,25])
plt.yticks(np.append(plt.yticks()[0], 23))
plt.xlabel("Time (s)")
plt.ylabel("Number of Nodes Discovered")
plt.title("Multicast-based Cumulative Node Discovery Time")
plt.legend()
plt.grid(True)
save_publication_figure('nm-scalability-default')
plt.show()


# 5% PACKET LOSS
# Generate cumulative discovery time graph
plt.figure(figsize=(10, 6))
for i, run in enumerate(network_manager_netem_5_data[:10]):
    if len(run) > 0:
        cumulative_times = np.arange(1, len(run) + 1)
        plt.plot(run, cumulative_times, label=f"Run {i+1}", alpha=0.7)

plt.xlim(left=0)
plt.ylim(bottom=1)
plt.yticks([1, 5, 10, 15, 20, 23,25])
plt.yticks(np.append(plt.yticks()[0], 23))
plt.xlabel("Time (s)")
plt.ylabel("Number of Nodes Discovered")
plt.title("Multicast-based Cumulative Node Discovery Time - 5% packet loss")
plt.legend()
plt.grid(True)
save_publication_figure('nm-scalability-5-pl')
plt.show()

# 10% PACKET LOSS
# Generate cumulative discovery time graph
plt.figure(figsize=(10, 6))
for i, run in enumerate(network_manager_netem_10_data[:10]):
    if len(run) > 0:
        cumulative_times = np.arange(1, len(run) + 1)
        plt.plot(run, cumulative_times, label=f"Run {i+1}", alpha=0.7)

plt.xlim(left=0)
plt.ylim(bottom=1)
plt.yticks([1, 5, 10, 15, 20, 23,25])
plt.yticks(np.append(plt.yticks()[0], 23))
plt.xlabel("Time (s)")
plt.ylabel("Number of Nodes Discovered")
plt.title("Multicast-based Cumulative Node Discovery Time - 10% packet loss")
plt.legend()
plt.grid(True)
save_publication_figure('nm-scalability-10-pl')
plt.show()

# 25% PACKET LOSS
# Generate cumulative discovery time graph
plt.figure(figsize=(10, 6))
for i, run in enumerate(network_manager_netem_25_data[:10]):
    if len(run) > 0:
        cumulative_times = np.arange(1, len(run) + 1)
        plt.plot(run, cumulative_times, label=f"Run {i+1}", alpha=0.7)

plt.xlim(left=0)
plt.ylim(bottom=1)
plt.yticks([1, 5, 10, 15, 20, 23,25])
plt.yticks(np.append(plt.yticks()[0], 23))
plt.xlabel("Time (s)")
plt.ylabel("Number of Nodes Discovered")
plt.title("Multicast-based Cumulative Node Discovery Time - 25% packet loss")
plt.legend()
plt.grid(True)
save_publication_figure('nm-scalability-25-pl')
plt.show()

# NEUROPIL
# Generate cumulative discovery time graph
plt.figure(figsize=(10, 6))
for i, run in enumerate(neuropil_default_data[:10]):
    if len(run) > 0:
        cumulative_times = np.arange(1, len(run) + 1)
        plt.plot(run, cumulative_times, label=f"Run {i+1}", alpha=0.7)

plt.xlim(left=39)
plt.ylim(bottom=1)
plt.xlabel("Time (s)")
plt.yticks([1, 4, 8, 12, 14])
plt.ylabel("Number of Nodes Discovered")
plt.title("DHT-based Cumulative Node Discovery Time")
plt.legend()
plt.grid(True)
save_publication_figure('np-scalability-default')
plt.show()

# NEUROPIL 2
# Generate cumulative discovery time graph
plt.figure(figsize=(10, 6))
for i, run in enumerate(neuropil_default_data_2[:10]):
    if len(run) > 0:
        cumulative_times = np.arange(1, len(run) + 1)
        plt.plot(run, cumulative_times, label=f"Run {i+1}", alpha=0.7)

plt.xlim(left=39)
plt.ylim(bottom=1)
plt.xlabel("Time (s)")
plt.yticks([1, 4, 8, 12, 14])
plt.ylabel("Number of Nodes Discovered")
plt.title("DHT-based Cumulative Node Discovery Time 2")
plt.legend()
plt.grid(True)
save_publication_figure('np-scalability-default-2')
plt.show()

# Generate cumulative discovery time graph
plt.figure(figsize=(10, 6))
for i, run in enumerate(neuropil_netem_10_data[:10]):
    if len(run) > 0:
        cumulative_times = np.arange(1, len(run) + 1)
        plt.plot(run, cumulative_times, label=f"Run {i+1}", alpha=0.7)

plt.xlim(left=39)
plt.ylim(bottom=1)
plt.xlabel("Time (s)")
plt.yticks([1, 4, 8, 12, 14])
plt.ylabel("Number of Nodes Discovered")
plt.title("DHT-based Cumulative Node Discovery Time - 10% packet loss")
plt.legend()
plt.grid(True)
save_publication_figure('np-scalability-pl-10')
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
plt.xlabel("Discovery Time (s)")
plt.title("Time Range to Discover Each Number of Nodes")
plt.grid(True)
plt.xlim(0, 28)
# Improve x-axis readability
# plt.xticks(sorted_node_counts, rotation=45)
save_publication_figure('nm-scalability-boxplot-default')
plt.show()


nodes_discovery_time_5 = defaultdict(list)

# Iterate over each run and collect times for each cumulative node count
for run in network_manager_netem_5_data:
    for i, time in enumerate(run):
        nodes_discovery_time_5[i + 1].append(time)  # Store discovery times for node count i+1
# Sort by node count (keys)
sorted_node_counts = sorted(nodes_discovery_time_5.keys())
boxplot_data = [nodes_discovery_time_5[n] for n in sorted_node_counts]
# Generate box plot
plt.figure(figsize=(12, 6))
plt.boxplot(boxplot_data, positions=sorted_node_counts, vert=False,  showfliers=True, patch_artist=True)
plt.ylabel("Number of Nodes Discovered")
plt.xlabel("Discovery Time (s)")
plt.title("Multicast-based - Time Range to Discover Each Number of Nodes - 5% packet loss")
plt.grid(True)
plt.xlim(0, 28)
# Improve x-axis readability
# plt.xticks(sorted_node_counts, rotation=45)
save_publication_figure('nm-scalability-boxplot-pl-5')
plt.show()

nodes_discovery_time_10 = defaultdict(list)

# Iterate over each run and collect times for each cumulative node count
for run in network_manager_netem_10_data:
    for i, time in enumerate(run):
        nodes_discovery_time_10[i + 1].append(time)  # Store discovery times for node count i+1

# Sort by node count (keys)
sorted_node_counts = sorted(nodes_discovery_time_10.keys())
boxplot_data = [nodes_discovery_time_10[n] for n in sorted_node_counts]

# Generate box plot
plt.figure(figsize=(12, 6))
plt.boxplot(boxplot_data, positions=sorted_node_counts, vert=False, showfliers=True, patch_artist=True)
plt.ylabel("Number of Nodes Discovered")
plt.xlabel("Discovery Time (s)")
plt.title("Multicast-based - Time Range to Discover Each Number of Nodes - 10% packet loss")
plt.grid(True)
plt.xlim(0, 28)
save_publication_figure('nm-scalability-boxplot-pl-10')
plt.show()

nodes_discovery_time_25 = defaultdict(list)

# Iterate over each run and collect times for each cumulative node count
for run in network_manager_netem_25_data:
    for i, time in enumerate(run):
        nodes_discovery_time_25[i + 1].append(time)  # Store discovery times for node count i+1

# Sort by node count (keys)
sorted_node_counts = sorted(nodes_discovery_time_25.keys())
boxplot_data = [nodes_discovery_time_25[n] for n in sorted_node_counts]

# Generate box plot
plt.figure(figsize=(12, 6))
plt.boxplot(boxplot_data, positions=sorted_node_counts,vert=False, showfliers=True, patch_artist=True)
plt.ylabel("Number of Nodes Discovered")
plt.xlabel("Discovery Time (s)")
plt.title("Multicast-based - Time Range to Discover Each Number of Nodes - 25% packet loss")
plt.grid(True)
plt.xlim(0, 28)
save_publication_figure('nm-scalability-boxplot-pl-25')
plt.show()

# #----Neuropil----
# nodes_discovery_time_neuropil = defaultdict(list)
# # Iterate over each run and collect times for each cumulative node count
# for run in neuropil_default_data:
#     for i, time in enumerate(run):
#         nodes_discovery_time_neuropil[i + 1].append(time)  # Store discovery times for node count i+1

# # Sort by node count (keys)
# sorted_node_counts = sorted(nodes_discovery_time_neuropil.keys())
# boxplot_data = [nodes_discovery_time_neuropil[n] for n in sorted_node_counts]

# # Generate box plot
# plt.figure(figsize=(12, 6))
# plt.boxplot(boxplot_data, positions=sorted_node_counts,vert=False, showfliers=True, patch_artist=True)
# plt.ylabel("Number of Nodes Discovered")
# plt.xlabel("Discovery Time (s)")
# plt.title("Neuropil - Time Range to Discover Each Number of Nodes")
# plt.grid(True)
# plt.show()

# #----Neuropil 10% Packet Loss----
# nodes_discovery_time_neuropil = defaultdict(list)
# # Iterate over each run and collect times for each cumulative node count
# for run in neuropil_netem_10_data:
#     for i, time in enumerate(run):
#         nodes_discovery_time_neuropil[i + 1].append(time)  # Store discovery times for node count i+1

# # Sort by node count (keys)
# sorted_node_counts = sorted(nodes_discovery_time_neuropil.keys())
# boxplot_data = [nodes_discovery_time_neuropil[n] for n in sorted_node_counts]

# # Generate box plot
# plt.figure(figsize=(12, 6))
# plt.boxplot(boxplot_data, positions=sorted_node_counts,vert=False, showfliers=True, patch_artist=True)
# plt.ylabel("Number of Nodes Discovered")
# plt.xlabel("Discovery Time (s)")
# plt.title("Neuropil - Time Range to Discover Each Number of Nodes - 10% packet loss")
# plt.grid(True)
# plt.show()