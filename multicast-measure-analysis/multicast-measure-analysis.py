import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

# Add this function after your imports and other setup code

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
    
    # Configure seaborn to use same colors
    sns.set_palette([colors['primary'], colors['secondary'], colors['tertiary'], colors['highlight']])
    
    return colors

def create_histogram(data, title, bins=20, kde=False, freq_count=False, color=None, filter=True, use_seaborn=True):
    """Create a standardized histogram with consistent styling.
    
    Args:
        data: The data array to plot
        title: Plot title
        filename: If provided, save to this filename (without extension)
        bins: Number of histogram bins
        kde: Whether to show KDE curve
        use_seaborn: Whether to use seaborn (True) or matplotlib (False)
        color: Optional specific color to use
    """
    plt.figure(figsize=(10, 6))
    
    # Get statistics
    # data = np.round(data, 3)
    mean = np.mean(data)
    std_dev = np.std(data)
    percentile_5, percentile_95 = np.percentile(data, [5, 95])
    filtered_data = data

    if filter:
        # Filter data within 95th percentile
        filtered_data = filtered_data[(data >= percentile_5)]
        filtered_data = filtered_data[(data <= percentile_95)] 
        print(f"Filtered Data: {len(filtered_data)} samples within 5th to 95th percentile")
    
    # Use consistent histogram style based on chosen method
    if use_seaborn:
        ax = sns.histplot(filtered_data, kde=kde, bins=bins, color=color or COLORS['primary'])
        if freq_count:
            # Get the current Axes object and get the height of each bar
            ax = plt.gca()
            for p in ax.patches:
                # Get height and position
                height = p.get_height()
                if height > 0:  # Only annotate non-empty bins
                    # Position the text at the center of each bar, slightly above
                    x = p.get_x() + p.get_width() / 2
                    y = height
                    # Add the count as text
                    ax.annotate(f'{int(height)}', (x, y), ha='center', va='bottom')
    else:
        counts, bins, patches = plt.hist(filtered_data, bins=bins, 
                                            color=color or COLORS['primary'], 
                                            edgecolor='black', 
                                            rwidth=0.9)
        # Annotate frequencies on the bars if using matplotlib
        if freq_count:
            for count, patch in zip(counts, patches):
                if count != 0:
                    x = patch.get_x() + patch.get_width() / 2
                    plt.text(x, count, f"{int(count)}", ha='center', va='bottom')
    
    # Consistent styling
    plt.title(title)
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (count)')
    plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    
    # Add footer with statistics
    # plt.subplots_adjust(bottom=0.15)
    # plt.figtext(0.5, 0.01, 
    #            f"n={len(data)}. Mean={mean:.3f}s, σ={std_dev:.3f}s. 5th-95th percentiles: [{percentile_5:.3f}, {percentile_95:.3f}]",
    #            ha='center', fontsize=9, style='italic')

    # Display the plot (but don't close it so caller can modify further)
    plt.tight_layout()
    plt.draw()
    
    # Return the figure and axes objects along with stats for further modifications
    fig = plt.gcf()
    ax = plt.gca()
    return mean, std_dev, percentile_5, percentile_95, fig, ax

def compare_histograms(datasets, labels, title, filename=None, bins=20, kde=False, colors=None, alphas=None):
    """Plot multiple histograms on the same figure for comparison.
    
    Args:
        datasets: List of data arrays to plot
        labels: List of labels for each dataset
        title: Plot title
        filename: Optional filename to save the plot
        bins: Number of bins for histograms
        kde: Whether to show KDE curves
    """
    plt.figure(figsize=(10, 6))
    
    # Use default colors if none provided
    if colors is None:
        colors = [COLORS['primary'], COLORS['secondary'], COLORS['tertiary'], COLORS['highlight']]
    
    # Use default alphas if none provided  
    if alphas is None:
        alphas = [0.7] * len(datasets)
    
    # Plot each histogram
    for i, data in enumerate(datasets):
        if i < len(colors) and i < len(labels):
            sns.histplot(data, bins=bins, kde=kde,
                        color=colors[i], label=labels[i])
    
    plt.title(title)
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (count)')
    plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    plt.legend()
    
    if filename:
        save_publication_figure(filename)
    
    plt.tight_layout()
    return plt.gca()

# Load the data from a file
def load_data(file_path):
    data = pd.read_csv(file_path)
    return data['multicast_benchmark_time_samples']

def load_boxdata(file_path):
    boxdata= {}
    with open(file_path, 'r') as file:
        lines = file.readlines()
        current_key = None
        for line in lines:
            line = line.strip()
            if line.startswith("multicast_benchmark_time_samples"):
                current_key = float(line.split()[-1])
                boxdata[current_key] = []
            else:
                if current_key is not None:
                    boxdata[current_key].append(float(line))
    return boxdata

def create_boxplot(data, title):
        # clean the data
    for key, values in data.items():
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        data[key] = [x for x in values if lower_bound <= x <= upper_bound]


    # Extract keys (timestamps) and values (samples)
    timestamps = sorted(data.keys())
    samples = [data[t] for t in timestamps]

    # Create the box plot
    plt.figure(figsize=(12, 6))
    plt.boxplot(samples, positions=timestamps, widths=0.2, vert=True, patch_artist=True)

    # Customize the plot
    plt.xlabel('Time waited after destroying Network Manager pod (s)')
    plt.ylabel('Discovery time (s)')
    plt.title(title)
    plt.xticks(timestamps)
    plt.grid(axis='y')
    # Show the plot
    plt.tight_layout()
    plt.draw()
    ax = plt.gca()
    fig = plt.gcf()

    return ax,fig

# Define consistent bin widths for packet loss data
def generate_bin_edges(min_val, max_val, target_bins=30):
    """Generate clean bin edges with round numbers."""
    # Round to nearest 0.5s for discovery time
    min_val = np.floor(min_val * 2) / 2
    max_val = np.ceil(max_val * 2) / 2
    return np.linspace(min_val, max_val, target_bins + 1)

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

# Plot the distribution and calculate statistics
def analyze_distribution(data, number):
    data = np.round(data, 3)
    # Basic statistics
    mean = np.mean(data)
    std_dev = np.std(data)
    percentile_5, percentile_95 = np.percentile(data, [5, 95])  # Calculate 5th and 95th percentiles
    
    print(f"Mean: {mean}")
    print(f"Standard Deviation: {std_dev}")
    print(f"5th Percentile: {percentile_5}, 95th Percentile: {percentile_95}")
    filtered_data = data
    # Filter data within 95th percentile
    # filtered_data = data[(data >= percentile_5)]
    # filtered_data = filtered_data[(data <= percentile_95)] 
    # print(f"Filtered Data: {len(filtered_data)} samples within 5th to 95th percentile")

    # Plot the distribution (of FILTERED DATA)
    counts, bins, patches = plt.hist(filtered_data, bins=100, color='skyblue', edgecolor='black', rwidth=0.9)
    # sns.histplot(filtered_data, kde=False, bins=20)
    # plt.axvline(percentiles[0], color='red', linestyle='--', label='5th Percentile')
    # plt.axvline(percentiles[1], color='green', linestyle='--', label='95th Percentile')
    # plt.legend()
    plt.xticks(ticks=range(3,19,2), minor=True)
    plt.title(f'Distribution of Time Samples in Total time benchmark with {number}% packet loss')
    plt.xlabel('Time(s)')
    plt.ylabel('Frequency(n of samples)')
    plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

    # Annotate frequencies on the bars
    for count, patch in zip(counts, patches):
        if count != 0:
            x = patch.get_x() + patch.get_width() / 2  # Center of the bar
            plt.text(x, count, f"{int(count)}", ha='center', va='bottom')       
    plt.show()

def analyze_distribution_default(data):
    data = np.round(data, 3)
    # Basic statistics
    mean = np.mean(data)
    std_dev = np.std(data)
    percentile_5, percentile_95 = np.percentile(data, [5, 95])  # Calculate 5th and 95th percentiles
    
    print(f"Mean: {mean}")
    print(f"Standard Deviation: {std_dev}")
    print(f"5th Percentile: {percentile_5}, 95th Percentile: {percentile_95}")
    filtered_data = data
    # Filter data within 95th percentile
    filtered_data = data[(data >= percentile_5)]
    filtered_data = filtered_data[(data <= percentile_95)] 
    print(f"Filtered Data: {len(filtered_data)} samples within 5th to 95th percentile")

    # Plot the distribution (of FILTERED DATA)
    #counts, bins, patches = plt.hist(filtered_data, bins='auto', color='skyblue', edgecolor='black', rwidth=0.9)
    sns.histplot(filtered_data, kde=True, bins=20)
    # plt.axvline(percentiles[0], color='red', linestyle='--', label='5th Percentile')
    # plt.axvline(percentiles[1], color='green', linestyle='--', label='95th Percentile')
    # plt.legend()
    # plt.xticks(ticks=range(3,19,2), minor=True)
    plt.title(f'Distribution of Time Samples in Total time benchmark\n')
    plt.xlabel('Time(s)')
    plt.ylabel('Frequency(n of samples)')
    plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    plt.show()

# Main function
def main():
    # Initialize consistent styling
    global COLORS
    COLORS = setup_publication_style()

    nm_default = load_data('../multicast-measures/results/netmanager_benchmark_results_overall.txt')
    nm_netem_5 = load_data('../multicast-measures/results/netmanager_benchmark_results_netem_5.txt')
    nm_netem_10 = load_data('../multicast-measures/results/netmanager_benchmark_results_netem_10.txt')
    nm_netem_25 = load_data('../multicast-measures/results/netmanager_benchmark_results_netem_25.txt')
    nm_default_baremetal = load_data('../multicast-measures/results/netmanager_benchmark_results_overall_baremetal.txt')
    nm_netem_5_baremetal = load_data('../multicast-measures/results/netmanager_benchmark_results_netem_baremetal_5.txt')
    nm_netem_10_baremetal = load_data('../multicast-measures/results/netmanager_benchmark_results_netem_baremetal_10.txt')
    nm_netem_25_baremetal = load_data('../multicast-measures/results/netmanager_benchmark_results_netem_baremetal_25.txt')
    np_default = load_data('../multicast-measures/results/neuropil-default.txt')
    # np_netem_5 = load_data('../multicast-measures/results/neuropil-netem-5.txt')
    np_netem_10 = load_data('../multicast-measures/results/neuropil-netem-10.txt')
    np_netem_10_both = load_data('../multicast-measures/results/neuropil-netem-both-10.txt')
    nm_range_big = load_boxdata('../multicast-measures/results/fluidos-range-big-server.txt')
    nm_range_vm = load_boxdata('../multicast-measures/results/netmanager_benchmark_results_range_step_02.txt')

    # Find overall min/max across all packet loss datasets
    all_pl_data = np.concatenate([
        nm_netem_5_baremetal[1:], 
        nm_netem_10_baremetal[1:],
        nm_netem_25_baremetal[1:],
        nm_netem_5[1:],
        nm_netem_10[1:],
        nm_netem_25[1:]
    ])
    min_val = np.min(all_pl_data)
    max_val = np.max(all_pl_data)
    consistent_bins = generate_bin_edges(min_val, max_val, 100)
    pl_bins = consistent_bins
# ------------------------------------NETWORK MANAGER------------------------------------

    # bins for nm vm baseline should go from 2.956 to 2.972 with 0.001 step
    default_nm_vm_bins = np.arange(2.956, 2.972, 0.001)

    # Default VM environment
    print("\nNetwork Manager - Default VM Environment:")
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_default[1:], 
                    'Node Discovery Time Distribution \n Multicast-based protocol in VM',
                    bins=default_nm_vm_bins)
        # Save if filename provided
    ax.yaxis.set_major_locator(ticker.MultipleLocator(2))
    save_publication_figure('nm_default_vm')
    
    # bins for nm vm baseline should go from 2.82 to 2.92 with 0.005 step
    default_nm_baremetal_bins = np.arange(2.82, 2.92, 0.005)

    # Baremetal environment
    print("\nNetwork Manager - Baremetal Environment:")
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_default_baremetal[1:], 
                    'Node Discovery Time Distribution \n Multicast-based protocol in Baremetal environment',
                    bins=default_nm_baremetal_bins)
    # Save if filename provided
    save_publication_figure('nm_default_baremetal')
    plt.show()
    
    # bins for nm analysis shold have a definition of 100ms, so from 2 to 20 with 0.1 step
    nm_netem_bins = np.arange(2, 20, 0.1)

    # With 5% packet loss
    print("\nNetwork Manager - 5% Packet Loss:")
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_netem_5_baremetal[1:], 
                    'Node Discovery Time Distribution \n Multicast-based Protocol With 5% Packet Loss - Baremetal',
                    bins=nm_netem_bins,
                    freq_count=False,
                    filter=False)
    # Save the zoomed-in figure first
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5,1))
    ax.set_xlim(0,9)
    save_publication_figure('nm_5_pl_baremetal')
    # extended
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_netem_5_baremetal[1:], 
                'Node Discovery Time Distribution \n Multicast-based Protocol With 5% Packet Loss - Baremetal',
                bins=nm_netem_bins,
                freq_count=False,
                filter=False)
    # Now expand the axis for the second figure
    #ax.set_xlim(0, 18)  # Set extended x-axis limits
    ax.set_xticks(range(1, 20, 1), minor=False)
    ax.set_xticks(np.arange(1.5, 18.5, 1.0), minor=True)
    ax.grid(True, which='both', linestyle='--', alpha=0.7)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    # Update the figure with extended limits
    plt.draw()
    # Save the modified figure with extended axis
    save_publication_figure('nm_5_pl_baremetal_extended_axis')
    plt.show()
    
    # With 10% packet loss
    print("\nNetwork Manager - 10% Packet Loss:")
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_netem_10_baremetal[1:], 
                    'Node Discovery Time Distribution \n Multicast-based Protocol With 10% Packet Loss - Baremetal',
                    bins=nm_netem_bins,
                    freq_count=False,
                    filter=False)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5,1))
    ax.set_xlim(0,14)
    save_publication_figure('nm_10_pl_baremetal')
    
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_netem_10_baremetal[1:], 
                    'Node Discovery Time Distribution \n Multicast-based Protocol With 10% Packet Loss - Baremetal',
                    bins=nm_netem_bins,
                    freq_count=False,
                    filter=False)
        # Now expand the axis for the second figure
    #ax.set_xlim(0, 18)  # Set extended x-axis limits
    ax.set_xticks(range(1, 20, 1), minor=False)
    ax.set_xticks(np.arange(1.5, 18.5, 1.0), minor=True)
    ax.grid(True, which='both', linestyle='--', alpha=0.7)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    # Update the figure with extended limits
    plt.draw()
    # Save the modified figure with extended axis
    save_publication_figure('nm_10_pl_baremetal_extended_axis')
    plt.show()
    
    # With 25% packet loss
    print("\nNetwork Manager - 25% Packet Loss:")
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_netem_25_baremetal[1:], 
                    'Node Discovery Time Distribution \n Multicast-based Protocol With 25% Packet Loss - Baremetal',
                    bins=nm_netem_bins,
                    freq_count=False,
                    filter=False)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5,1))
    ax.set_xlim(0,19)
    save_publication_figure('nm_25_pl_baremetal')
    
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_netem_25_baremetal[1:], 
                    'Node Discovery Time Distribution \n Multicast-based Protocol With 25% Packet Loss - Baremetal',
                    bins=nm_netem_bins,
                    freq_count=False,
                    filter=False)
    #ax.set_xlim(0, 18)  # Set extended x-axis limits
    ax.set_xticks(range(1, 20, 1), minor=False)
    ax.set_xticks(np.arange(1.5, 18.5, 1.0), minor=True)
    ax.grid(True, which='both', linestyle='--', alpha=0.7)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    # Update the figure with extended limits
    plt.draw()
    # Save the modified figure with extended axis
    save_publication_figure('nm_25_pl_baremetal_extended_axis')
    plt.show()

# ------------------------------------VMs------------------------------------
    # With 5% packet loss
    print("\nNetwork Manager - 5% Packet Loss:")
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_netem_5[1:], 
                    'Node Discovery Time Distribution \n Multicast-based Protocol With 5% Packet Loss - VM',
                    bins=nm_netem_bins,
                    freq_count=False,
                    filter=False)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5,1))
    ax.set_xlim(0,14)
    save_publication_figure('nm_5_pl')
    
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_netem_5[1:], 
                    'Node Discovery Time Distribution \n Multicast-based Protocol With 5% Packet Loss - VM',
                    bins=nm_netem_bins,
                    freq_count=False,
                    filter=False)
    #ax.set_xlim(0, 18)  # Set extended x-axis limits
    ax.set_xticks(range(1, 20, 1), minor=False)
    ax.set_xticks(np.arange(1.5, 18.5, 1.0), minor=True)
    ax.grid(True, which='both', linestyle='--', alpha=0.7)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    # Update the figure with extended limits
    plt.draw()
    # Save the modified figure with extended axis
    save_publication_figure('nm_5_pl_extended_axis')
    plt.show()
    
    # With 10% packet loss
    print("\nNetwork Manager - 10% Packet Loss:")
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_netem_10[1:], 
                    'Node Discovery Time Distribution \n Multicast-based Protocol With 10% Packet Loss - VM',
                    bins=nm_netem_bins,
                    freq_count=False,
                    filter=False)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5,1))
    ax.set_xlim(0,14)
    save_publication_figure('nm_10_pl')
    
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_netem_10[1:], 
                    'Node Discovery Time Distribution \n Multicast-based Protocol With 10% Packet Loss - VM',
                    bins=nm_netem_bins,
                    freq_count=False,
                    filter=False)
    #ax.set_xlim(0, 18)  # Set extended x-axis limits
    ax.set_xticks(range(1, 20, 1), minor=False)
    ax.set_xticks(np.arange(1.5, 18.5, 1.0), minor=True)
    ax.grid(True, which='both', linestyle='--', alpha=0.7)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    # Update the figure with extended limits
    plt.draw()
    # Save the modified figure with extended axis
    save_publication_figure('nm_10_pl_extended_axis')
    plt.show()
    
    # With 25% packet loss
    print("\nNetwork Manager - 25% Packet Loss:")
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_netem_25[1:], 
                    'Node Discovery Time Distribution \n Multicast-based Protocol With 25% Packet Loss - VM',
                    bins=nm_netem_bins,
                    freq_count=False,
                    filter=False)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5,1))
    ax.set_xlim(0,19)
    save_publication_figure('nm_25_pl')
    
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(nm_netem_25[1:], 
                'Node Discovery Time Distribution \n Multicast-based Protocol With 25% Packet Loss - VM',
                bins=nm_netem_bins,
                freq_count=False,
                filter=False)
    #ax.set_xlim(0, 18)  # Set extended x-axis limits
    ax.set_xticks(range(1, 20, 1), minor=False)
    ax.set_xticks(np.arange(1.5, 18.5, 1.0), minor=True)
    ax.grid(True, which='both', linestyle='--', alpha=0.7)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    # Update the figure with extended limits
    plt.draw()
    # Save the modified figure with extended axis
    save_publication_figure('nm_25_pl_extended_axis')
    plt.show()

    # compare_histograms(
    # [nm_default_baremetal[1:], nm_netem_5_baremetal[1:], 
    #  nm_netem_10_baremetal[1:], nm_netem_25_baremetal[1:]],
    # ["0% Packet Loss", "5% Packet Loss", "10% Packet Loss", "25% Packet Loss"],
    # "Impact of Packet Loss on Discovery Time - Baremetal",
    # "packet_loss_comparison_baremetal",
    # bins=30
    # )
    # plt.show()

# ------------------------------------NEUROPIL------------------------------------
#    # Default VM environment

    np_default_bins = np.arange(30,65,1)

    print("\nNeuropil - Default VM Environment:")
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(np_default, 
                    'Node Discovery Time Distribution \n DHT-based Protocol - VM',
                    bins=np_default_bins,
                    freq_count=False,
                    filter=False)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    save_publication_figure('np_default_vm')

    np_netem_10_bins = np.arange(30,100,1)

    # With 10% packet loss
    print("\nNeuropil - 10% Packet Loss:")
    mean, std_dev, percentile_5, percentile_95, fig, ax = create_histogram(np_netem_10_both,
                    'Node Discovery Time Distribution \n DHT-based Protocol With 10% Packet Loss - VM',
                    bins=np_netem_10_bins,
                    freq_count=False,
                    filter=False)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    save_publication_figure('np_10_pl')

#------------------------------------BOX PLOT------------------------------------

    # ax,fig = create_boxplot(nm_range_vm, 'Multicast-based in VM environment')
    # ax, fig = create_boxplot(nm_range_big, 'Multicast-based in Baremetal environment')



# ------------------------------------Network Manager DEFAULT VM------------------------------------
#     plt.figure(figsize=(10, 6))
#     data = np.round(nm_default, 3)
#     # Basic statistics
#     mean = np.mean(data)
#     std_dev = np.std(data)
#     percentile_5, percentile_95 = np.percentile(data, [5, 95])  # Calculate 5th and 95th percentiles

#     print(f"Mean: {mean}")
#     print(f"Standard Deviation: {std_dev}")
#     print(f"5th Percentile: {percentile_5}, 95th Percentile: {percentile_95}")
#     filtered_data = data
#     # Filter data within 95th percentile
#     filtered_data = data[(data >= percentile_5)]
#     filtered_data = filtered_data[(data <= percentile_95)] 
#     print(f"Filtered Data: {len(filtered_data)} samples within 5th to 95th percentile")

#     # Plot the distribution (of FILTERED DATA)
#     #counts, bins, patches = plt.hist(filtered_data, bins='auto', color='skyblue', edgecolor='black', rwidth=0.9)
#     sns.histplot(filtered_data, kde=False, bins=20)
#     # plt.axvline(percentiles[0], color='red', linestyle='--', label='5th Percentile')
#     # plt.axvline(percentiles[1], color='green', linestyle='--', label='95th Percentile')
#     # plt.legend()
#     # plt.xticks(ticks=range(3,19,2), minor=True)
#     plt.title(f'Node Discovery Time Distribution - Multicast-based protocol in VM \n')
#     plt.xlabel('Time (s)')
#     plt.ylabel('Frequency (count)')
#     plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
#     plt.show()

# # ------------------------------------Network Manager DEFAULT BAREMETAL------------------------------------

#     plt.figure(figsize=(10, 6))
#     data = np.round(nm_default_baremetal, 3)
#     # Basic statistics
#     mean = np.mean(data)
#     std_dev = np.std(data)
#     percentile_5, percentile_95 = np.percentile(data, [5, 95])  # Calculate 5th and 95th percentiles

#     print(f"Mean: {mean}")
#     print(f"Standard Deviation: {std_dev}")
#     print(f"5th Percentile: {percentile_5}, 95th Percentile: {percentile_95}")
#     filtered_data = data
#     # Filter data within 95th percentile
#     filtered_data = data[(data >= percentile_5)]
#     filtered_data = filtered_data[(data <= percentile_95)] 
#     print(f"Filtered Data: {len(filtered_data)} samples within 5th to 95th percentile")

#     # Plot the distribution (of FILTERED DATA)
#     #counts, bins, patches = plt.hist(filtered_data, bins='auto', color='skyblue', edgecolor='black', rwidth=0.9)
#     sns.histplot(filtered_data, kde=False, bins=20)
#     # plt.axvline(percentiles[0], color='red', linestyle='--', label='5th Percentile')
#     # plt.axvline(percentiles[1], color='green', linestyle='--', label='95th Percentile')
#     # plt.legend()
#     # plt.xticks(ticks=range(3,19,2), minor=True)
#     plt.title(f'Node Discovery Time Distribution - Multicast-based protocol in Baremetal environment \n')
#     plt.xlabel('Time (s)')
#     plt.ylabel('Frequency (count)')
#     plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
#     plt.show()

# # ------------------------------------NetworkManager with Packet Loss------------------------------------

#     # 5% packet loss
#     plt.figure(figsize=(10, 6))
#     data = np.round(nm_netem_5, 3)
#     # Basic statistics
#     mean = np.mean(data)
#     std_dev = np.std(data)
#     percentile_5, percentile_95 = np.percentile(data, [5, 95])  # Calculate 5th and 95th percentiles

#     print(f"Mean: {mean}")
#     print(f"Standard Deviation: {std_dev}")
#     print(f"5th Percentile: {percentile_5}, 95th Percentile: {percentile_95}")
#     filtered_data = data
#     counts, bins, patches = plt.hist(filtered_data, bins=100, color='skyblue', edgecolor='black', rwidth=0.9)
#     # sns.histplot(filtered_data, kde=False, bins=20)
#     # plt.axvline(percentiles[0], color='red', linestyle='--', label='5th Percentile')
#     # plt.axvline(percentiles[1], color='green', linestyle='--', label='95th Percentile')
#     # plt.legend()
#     plt.xticks(ticks=range(3,19,2), minor=True)
#     plt.title(f'Node Discovery Time Distribution - Multicast-based Protocol With 5% Packet Loss \n')
#     plt.xlabel('Time (s)')
#     plt.ylabel('Frequency (count)')
#     plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

#     # Annotate frequencies on the bars
#     for count, patch in zip(counts, patches):
#         if count != 0:
#             x = patch.get_x() + patch.get_width() / 2  # Center of the bar
#             plt.text(x, count, f"{int(count)}", ha='center', va='bottom')       
#     plt.show()

#         # 10% packet loss
#     plt.figure(figsize=(10, 6))
#     data = np.round(nm_netem_10, 3)
#     # Basic statistics
#     mean = np.mean(data)
#     std_dev = np.std(data)
#     percentile_5, percentile_95 = np.percentile(data, [5, 95])  # Calculate 5th and 95th percentiles

#     print(f"Mean: {mean}")
#     print(f"Standard Deviation: {std_dev}")
#     print(f"5th Percentile: {percentile_5}, 95th Percentile: {percentile_95}")
#     filtered_data = data
#     counts, bins, patches = plt.hist(filtered_data, bins=20, color='skyblue', edgecolor='black', rwidth=0.9)
#     # sns.histplot(filtered_data, kde=False, bins=20)
#     # plt.axvline(percentiles[0], color='red', linestyle='--', label='5th Percentile')
#     # plt.axvline(percentiles[1], color='green', linestyle='--', label='95th Percentile')
#     # plt.legend()
#     plt.xticks(ticks=range(3,19,2), minor=True)
#     plt.title(f'Node Discovery Time Distribution - Multicast-based Protocol With 10% Packet Loss \n')
#     plt.xlabel('Time (s)')
#     plt.ylabel('Frequency (count)')
#     plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

#     # Annotate frequencies on the bars
#     for count, patch in zip(counts, patches):
#         if count != 0:
#             x = patch.get_x() + patch.get_width() / 2  # Center of the bar
#             plt.text(x, count, f"{int(count)}", ha='center', va='bottom')       
#     plt.show()

#         # 25% packet loss
#     plt.figure(figsize=(10, 6))
#     data = np.round(nm_netem_25, 3)
#     # Basic statistics
#     mean = np.mean(data)
#     std_dev = np.std(data)
#     percentile_5, percentile_95 = np.percentile(data, [5, 95])  # Calculate 5th and 95th percentiles

#     print(f"Mean: {mean}")
#     print(f"Standard Deviation: {std_dev}")
#     print(f"5th Percentile: {percentile_5}, 95th Percentile: {percentile_95}")
#     filtered_data = data
#     # counts, bins, patches = plt.hist(filtered_data, bins=30, color='skyblue', edgecolor='black', rwidth=0.9)
#     sns.histplot(filtered_data, kde=False, bins=20)
#     # plt.axvline(percentiles[0], color='red', linestyle='--', label='5th Percentile')
#     # plt.axvline(percentiles[1], color='green', linestyle='--', label='95th Percentile')
#     # plt.legend()
#     plt.xticks(ticks=range(0,19,2), minor=True)
#     plt.title(f'Node Discovery Time Distribution - Multicast-based Protocol With 25% Packet Loss \n')
#     plt.xlabel('Time (s)')
#     plt.ylabel('Frequency (count)')
#     plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

#     # Annotate frequencies on the bars
#     for count, patch in zip(counts, patches):
#         if count != 0:
#             x = patch.get_x() + patch.get_width() / 2  # Center of the bar
#             plt.text(x, count, f"{int(count)}", ha='center', va='bottom')       
#     plt.show()

    
    # CANDLE GRAPH
    # Path to the text file
    # file_path = '/home/vm1/app/tesi-analysis-tools/multicast-measures/results/netmanager_benchmark_results_netem_0-15.txt'
    # boxdata_0_15= {}
    # with open(file_path, 'r') as file:
    #     lines = file.readlines()
    #     current_key = None
    #     for line in lines:
    #         line = line.strip()
    #         if line.startswith("multicast_benchmark_time_samples"):
    #             current_key = float(line.split()[-1])
    #             boxdata_0_15[current_key] = []
    #         else:
    #             if current_key is not None:
    #                 boxdata_0_15[current_key].append(float(line))

    # clean the data
    # for key, values in boxdata_0_15.items():
    #     q1 = np.percentile(values, 25)
    #     q3 = np.percentile(values, 75)
    #     iqr = q3 - q1
    #     lower_bound = q1 - 1.5 * iqr
    #     upper_bound = q3 + 1.5 * iqr
    #     boxdata_0_15[key] = [x for x in values if lower_bound <= x <= upper_bound]


    # # Extract keys (timestamps) and values (samples)
    # timestamps = sorted(boxdata_0_15.keys())
    # samples = [boxdata_0_15[t] for t in timestamps]

    # # Create the box plot
    # plt.figure(figsize=(12, 6))
    # plt.boxplot(samples, positions=timestamps, widths=0.4, vert=True, patch_artist=True)

    # # Customize the plot
    # plt.xlabel('Time waited after destroying NetworkManager pod (s)')
    # plt.ylabel('Discovery time (s)')
    # plt.title('Candlestick (Box Plot) of Benchmark Time Samples')
    # plt.xticks(timestamps, rotation=45)
    # plt.grid(axis='y')
    # # Show the plot
    # plt.tight_layout()
    # plt.show()

    #-------------NEUROPIL-------------------

    # ---Neuropil DEFAULT
    # Basic statistics
    # plt.figure(figsize=(10, 6))
    # np_mean = np.mean(np_default)
    # nm_default_baremetal = np.mean(nm_default_baremetal)

    # np_std_dev = np.std(np_default)
    # nm_default_baremetal_std_dev = np.std(nm_default_baremetal)

    # np_percentile_5, np_percentile_95 = np.percentile(np_default, [5, 95])  # Calculate 5th and 95th percentiles
    # nm_default_baremetal_percentile_5, nm_default_baremetal_percentile_95 = np.percentile(nm_default_baremetal, [5, 95])
    
    # # Round values
    # np_default = np.round(np_default, 3)
    # nm_default_baremetal = np.round(nm_default_baremetal, 3)
    
    # print(f"Mean: {np_mean}")
    # print(f"Standard Deviation: {np_std_dev}")
    # print(f"5th Percentile: {np_percentile_5}, 95th Percentile: {np_percentile_95}")

    # print(f"Mean: {nm_default_baremetal}")
    # print(f"Standard Deviation: {nm_default_baremetal_std_dev}")
    # print(f"5th Percentile: {nm_default_baremetal_percentile_5}, 95th Percentile: {nm_default_baremetal_percentile_95}")

    # # Clean data
    # np_default_filtered = np_default
    # nm_default_baremetal_filtered = nm_default_baremetal

    # # Filter data within 95th percentile
    # np_default_filtered = np_default[(np_default >= np_percentile_5)]
    # np_default_filtered = np_default_filtered[(np_default <= np_percentile_95)] 
    # print(f"Filtered Data: {len(np_default_filtered)} samples within 5th to 95th percentile")

    # nm_default_baremetal_filtered = nm_default_baremetal[(nm_default_baremetal >= nm_default_baremetal_percentile_5)]
    # nm_default_baremetal_filtered = nm_default_baremetal_filtered[(nm_default_baremetal <= nm_default_baremetal_percentile_95)]
    # print(f"Filtered Data: {len(nm_default_baremetal_filtered)} samples within 5th to 95th percentile")
    
    # # Plot the distribution (of FILTERED DATA)
    # # counts, bins, patches = plt.hist(np_default_filtered, bins=100, color='skyblue', edgecolor='black', rwidth=0.9)
    # sns.histplot(np_default_filtered, kde=False, bins=100)
    # sns.histplot(nm_default_baremetal_filtered, kde=False, bins=1, color='red')

    # plt.legend(['Neuropil Default', 'NM Baremetal'])
    # # plt.xticks(ticks=range(3,19,2), minor=True)
    # plt.title(f'Distribution of Time Samples in Total time benchmark with 0% packet loss - Neuropil')
    # plt.xlabel('Time(s)')
    # plt.ylabel('Frequency(n of samples)')
    # plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

    # # Annotate frequencies on the bars
    # # for count, patch in zip(counts, patches):
    # #     if count != 0:
    # #         x = patch.get_x() + patch.get_width() / 2  # Center of the bar
    # #         plt.text(x, count, f"{int(count)}", ha='center', va='bottom')       
    # plt.show()


    # # NP BOTH 10%
    # plt.figure(figsize=(10, 6))
    # np_mean = np.mean(np_netem_10_both)
    # np_std_dev = np.std(np_netem_10_both)

    # np_percentile_5, np_percentile_95 = np.percentile(np_netem_10_both, [5, 95])  # Calculate 5th and 95th percentiles
  
    # # Round values
    # np_netem_10_both = np.round(np_netem_10_both, 3)
    
    # print(f"Mean: {np_mean}")
    # print(f"Standard Deviation: {np_std_dev}")
    # print(f"5th Percentile: {np_percentile_5}, 95th Percentile: {np_percentile_95}")
    # # Clean data
    # np_netem_10_both_filtered = np_netem_10_both
    # nm_default_baremetal_filtered = nm_default_baremetal

    # # Filter data within 95th percentile
    # np_netem_10_both_filtered = np_netem_10_both[(np_netem_10_both >= np_percentile_5)]
    # np_netem_10_both_filtered = np_netem_10_both_filtered[(np_netem_10_both <= np_percentile_95)] 
    # print(f"Filtered Data: {len(np_netem_10_both_filtered)} samples within 5th to 95th percentile")
    # # Plot the distribution (of FILTERED DATA)
    # # counts, bins, patches = plt.hist(np_default_filtered, bins=100, color='skyblue', edgecolor='black', rwidth=0.9)
    # sns.histplot(np_netem_10_both_filtered, kde=False, bins=100)

    # plt.legend()
    # # plt.xticks(ticks=range(3,19,2), minor=True)
    # plt.title(f'Distribution of Time Samples in Total time benchmark with 10% packet loss - Neuropil')
    # plt.xlabel('Time(s)')
    # plt.ylabel('Frequency(n of samples)')
    # plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

    # # Annotate frequencies on the bars
    # # for count, patch in zip(counts, patches):
    # #     if count != 0:
    # #         x = patch.get_x() + patch.get_width() / 2  # Center of the bar
    # #         plt.text(x, count, f"{int(count)}", ha='center', va='bottom')       
    # plt.show()

if __name__ == "__main__":
    main()
