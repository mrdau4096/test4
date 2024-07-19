import matplotlib.pyplot as plt
import pandas as pd
import sys

def parse_mprof_data(file_path):
    time_data = []
    memory_data = []
    functions = {}

    with open(file_path, 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) == 2 and parts[0] == "CMDLINE":
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
                continue
                func_name = parts[1].split(".")[-1]
                memory = float(parts[2])
                time = float(parts[3])
                try:
                    functions[func_name][0].append(memory)
                    functions[func_name][1].append(time)
                except KeyError:
                    functions[func_name] = ([memory,], [time,])

            else:
                print(f"Unexpected line format: {line.strip()}")

    return time_data, memory_data, functions

def plot_memory_usage(time_data, memory_data, functions):
    start_time = time_data[0]
    plt.figure(figsize=(10, 5))
    plt.plot([(time - start_time) / 60 for time in time_data], memory_data, label='Memory Utilisation')
    for func_name, (func_memory, func_time) in functions.items():
        plt.plot([(time - start_time) / 60 for time in func_time], func_memory, label=func_name)
    plt.xlabel('Time (Mins)')
    plt.ylabel('Memory Usage (MiB)')
    plt.title("NEA Project Memory Utilisation Grapher")
    plt.legend()
    plt.grid(True)
    plt.show()

try:
    # Read file path from command line argument
    if len(sys.argv) < 2:
        raise Exception("Usage: python profile_visualise.py <file_path>")
        sys.exit(1)
    file_path = sys.argv[1]
except Exception:
    file_path = "C:\\Users\\User\\Documents\\GitHub\\test4\\src\\profiler_data\\data\\" + input("Filepath\n> ")

time_data, memory_data, functions = parse_mprof_data(file_path)

# Debugging output
print(f"Parsed {len(time_data)} time points and {len(memory_data)} memory points.")
if time_data and memory_data:
    print(f"First time point: {time_data[0]}, First memory point: {memory_data[0]}")
    print(f"Last time point: {time_data[-1]}, Last memory point: {memory_data[-1]}")
    print(f"Time elapsed: {(int(time_data[-1] - time_data[0])) // 60}m, {int(round(time_data[-1] - time_data[0], 0)) % 60}s")
else:
    print("No data parsed. Please check the file format and contents.")

plot_memory_usage(time_data, memory_data, functions)
