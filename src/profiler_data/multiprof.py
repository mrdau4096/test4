import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import time

def parse_mprof_data(file_path):
    time_data = []
    memory_data = []

    with open(file_path, 'r') as file:
        for line in file:
            parts = line.split()
            if parts[0] == "CMDLINE":
                continue
            elif len(parts) == 3 and parts[0] == "MEM":  # MEM lines
                try:
                    memory = float(parts[1])
                    time = float(parts[2])
                    memory_data.append(memory)
                    time_data.append(time)
                except ValueError as e:
                    print(f"Skipping line due to ValueError: {line.strip()}")
                    print(f"Error: {e}")
            elif len(parts) == 7 and parts[0] == "FUNC":  # FUNC lines
                continue  # Skipping FUNC lines for now
            else:
                print(f"Unexpected line format: {line.strip()}")

    return memory_data, time_data

def plot_memory_usage(dataset):
    plt.figure(figsize=(10, 5))
    for name, mem, time in dataset:
        plt.plot([(ctime - time[0]) / 60 for ctime in time], mem, label=name)
    plt.xlabel('Time (Mins)')
    plt.ylabel('Memory Usage (MiB)')
    plt.title("NEA Project Memory Utilisation Grapher.")
    plt.legend()
    plt.grid(True)
    plt.show()

# Replace 'mprofile_*.dat' with your actual file name
file_paths = {
    "No GC": "mprofile_20240719201121",                 #No GC
    "GC": "mprofile_20240719201443",                    #With GC
    "GC, No Physics": "mprofile_20240719205509",        #No phys iterations, with GC
    "No GC, No Physics": "mprofile_20240719210006",     #No phys iterations, no GC
    "GC, No Physics, No UI": "mprofile_20240719210410", #No phys iterations, with GC, no UI
    "GC, No UI": "mprofile_20240719210801",             #With GC, no UI
    "No GC, No UI": "mprofile_20240719211109",          #No GC, no UI
}

dataset = []
for data_name, file in file_paths.items():
    mem, time = parse_mprof_data(f"C:\\Users\\User\\Documents\\GitHub\\test4\\src\\profiler_data\\data\\{file}.dat")
    dataset.append([data_name, mem, time])
    print(f"{data_name}; Parsed {len(time)} time points and {len(mem)} memory points.")
    if time and mem:
        print(f"First time point: {time[0]}, First memory point: {mem[0]}")
        print(f"Last time point: {time[-1]}, Last memory point: {mem[-1]}")
        print(f"Time elapsed: {(int(time[-1] - time[0])) // 60}m, {int(round(time[-1] - time[0], 0)) % 60}s")
    else:
        print(f"No {data_name} data parsed. Please check the file format and contents.")


plot_memory_usage(dataset)