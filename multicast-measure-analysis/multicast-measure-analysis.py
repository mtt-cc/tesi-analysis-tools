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
    # filtered_data = data[(data >= percentile_5)]
    # filtered_data = filtered_data[(data <= percentile_95)] 
    print(f"Filtered Data: {len(filtered_data)} samples within 5th to 95th percentile")

    # Plot the distribution (of FILTERED DATA)
    #counts, bins, patches = plt.hist(filtered_data, bins='auto', color='skyblue', edgecolor='black', rwidth=0.9)
    sns.histplot(filtered_data, kde=True, bins=30)
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
    file_paths = ['../multicast-measures/netmanager_benchmark_results_netem_baremetal_5.txt',
                  '../multicast-measures/netmanager_benchmark_results_netem_baremetal_25.txt',
                  '../multicast-measures/netmanager_benchmark_results_netem_baremetal_10.txt',
                  '../multicast-measures/netmanager_benchmark_results_overall_baremetal.txt',]
    for file_path in file_paths:
        data = load_data(file_path)
        if file_path == '../multicast-measures/netmanager_benchmark_results_overall.txt':
            analyze_distribution_default(data)
        else:
            number = file_path.split('_')[-1].split('.')[0]
            analyze_distribution(data, number)

    # generate candle graph

    # Path to the text file
    file_path = '/home/vm1/app/tesi-analysis-tools/multicast-measures/netmanager_benchmark_results_netem_0-15.txt'
    boxdata_0_15= {}
    with open(file_path, 'r') as file:
        lines = file.readlines()
        current_key = None
        for line in lines:
            line = line.strip()
            if line.startswith("multicast_benchmark_time_samples"):
                current_key = float(line.split()[-1])
                boxdata_0_15[current_key] = []
            else:
                if current_key is not None:
                    boxdata_0_15[current_key].append(float(line))

    # clean the data
    for key, values in boxdata_0_15.items():
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        boxdata_0_15[key] = [x for x in values if lower_bound <= x <= upper_bound]


    # Extract keys (timestamps) and values (samples)
    timestamps = sorted(boxdata_0_15.keys())
    samples = [boxdata_0_15[t] for t in timestamps]

    # Create the box plot
    plt.figure(figsize=(12, 6))
    plt.boxplot(samples, positions=timestamps, widths=0.4, vert=True, patch_artist=True)

    # Customize the plot
    plt.xlabel('Time waited after destroying NetworkManager pod (s)')
    plt.ylabel('Discovery time (s)')
    plt.title('Candlestick (Box Plot) of Benchmark Time Samples')
    plt.xticks(timestamps, rotation=45)
    plt.grid(axis='y')
    

    # Show the plot
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
