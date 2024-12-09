import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data from a file
def load_data(file_path):
    data = pd.read_csv(file_path)
    return data['multicast_benchmark_time_samples']

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
    sns.histplot(filtered_data, kde=True, bins='auto')
    # plt.axvline(percentiles[0], color='red', linestyle='--', label='5th Percentile')
    # plt.axvline(percentiles[1], color='green', linestyle='--', label='95th Percentile')
    # plt.legend()
    # plt.xticks(ticks=range(3,19,2), minor=True)
    plt.title(f'Distribution of Time Samples in Total time benchmark')
    plt.xlabel('Time(s)')
    plt.ylabel('Frequency(n of samples)')
    plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    plt.show()

# Main function
def main():
    file_paths = ['../multicast-measures/netmanager_benchmark_results_netem_5.txt',
                  '../multicast-measures/netmanager_benchmark_results_netem_10.txt',
                  '../multicast-measures/netmanager_benchmark_results_netem_25.txt',
                  '../multicast-measures/netmanager_benchmark_results_overall.txt',]
    for file_path in file_paths:
        data = load_data(file_path)
        if file_path == '../multicast-measures/netmanager_benchmark_results_overall.txt':
            analyze_distribution_default(data)
        else:
            number = file_path.split('_')[-1].split('.')[0]
            analyze_distribution(data, number)

if __name__ == "__main__":
    main()
