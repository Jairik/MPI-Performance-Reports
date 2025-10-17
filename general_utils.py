''' Helper functions for performance analysis '''

import subprocess
import os
import ctypes
import numpy as np
import plotly.graph_objects as go

executable: str = str('summation')  # Default value, make sure python knows that it's a string

def compile_mpi_program(filename: str = 'summation.c') -> None:
    ''' Attempt to compile the globally defined MPI C program using mpicc '''
    executable: str = filename.replace('.c', '')  # Derive executable name from filename
    try:
        subprocess.run(['mpicc', filename, '-o', executable], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        exit(1)

def run_executable(lib, x: int = 10000000, np: int = 4) -> str:
    ''' Attempt to run the globally defined executable using mpirun with a specified number of processes and x parameter '''
    try:
        result = subprocess.run(['mpirun', '-np', f'{np}', f'./{executable}', f'{x}'], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Execution failed: {e}")
        exit(1)
    return result.stdout  # Return the output for further processing

def parse_execution_output(lib, output: str, np: int, serial_time: float = None) -> dict:
    ''' Parse the output from the C program execution assign everything to a dictionary '''
    lines: list[str] = output.strip().split('\n')  # Split output into lines
    results: dict = {}  # Initialize results dictionary
    for line in lines:
        # Extract run time values
        if "run time" in line:
            # Extract per-core information for parallel programs
            if "MPI" in line:
                parts = line.split()  # Split line into parts by spaces
                rank = int(parts[5])  # Extract rank number, which should be at index 5
                time = float(parts[-1])  # Extract time value, which should be last
                results[f'rank {rank}'] = time  # Store in dictionary with rank as key
            # Extract serial information by seperate key
            elif "Serial" in line:
                parts = line.split()  # Split line into parts by spaces
                time = float(parts[-1])  # Extract time value, which should be last
                results['serial'] = time  # Store in dictionary with 'serial' as key
        # Extract total summation value
        elif "Summation" in line:
            parts = line.split()  # Split line into parts by spaces
            total = int(parts[-1])  # Extract total summation value, which should be last
            results['total'] = total  # Store in dictionary with 'total' as key
        # Extract the benchmarked fraction of parallelizable code value
        elif "Fraction of Parallel" in line:
            parts = line.split()  # Split line into parts by spaces
            fp = float(parts[-1]).round(5)  # Extract fraction value, which should be last
            results['fp'] = fp  # Store in dictionary with 'fp' as key
    
    add_all_stats_to_results(lib, results, np, serial_time)  # Add speedup, efficiency, and fraction parallel/serial to results (apply directly by reference)
    
    # Return the sorted results dictionary
    return dict(sorted(results.items(), key=lambda x: (isinstance(x[0], int), x[0])))

def add_all_stats_to_results(lib, results: dict, np: int, serial_time: float = None) -> None:
    ''' Derive the fraction of parallelizable code, speedup, and efficiency from the execution results '''
    # If this is for the serial process (no serial_time passed), we can skip calculations
    if serial_time:
        # Derive max parallel time
        parallel_times = [time for key, time in results.items() if isinstance(key, int) or key.startswith('rank ')]  # Get all parallel execution times
        max_parallel_time = max(parallel_times) if parallel_times else 0.0  # Use the maximum parallel time
        # Use helper function from C algorithms library to derive speedup, efficiency, and fraction parallelizable
        results['speedup'] = float(lib.getSpeedup(serial_time, max_parallel_time)).round(5)
        results['efficiency'] = float(lib.getEfficiency(results['speedup'], np)).round(5)
        results['fp'] = float(lib.getFractionParallelizable(serial_time, max_parallel_time, np)).round(5)
    # On first iteration for serial execution, we can skip calculations and set speedup and efficiency to 1
    else:
        results['speedup'] = 1.0  # Speedup is 1 for serial execution
        results['efficiency'] = 1.0  # Efficiency is 1 for serial
        results['fp'] = 0.0

def load_c_library(lib_path: str = "algorithmslib.so") -> ctypes.CDLL:
    ''' Load the C shared library for performance calculations '''
    lib = ctypes.CDLL(lib_path)
    # Declaring argument types
    lib.getSpeedup.argtypes = [ctypes.c_double, ctypes.c_double]
    lib.getEfficiency.argtypes = [ctypes.c_double, ctypes.c_int]
    lib.getAmdahlsLaw.argtypes = [ctypes.c_double, ctypes.c_double]
    lib.getFractionParallelizable.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_int]
    # Declaring the return types
    lib.getSpeedup.restype = ctypes.c_double
    lib.getEfficiency.restype = ctypes.c_double
    lib.getAmdahlsLaw.restype = ctypes.c_double
    lib.getFractionParallelizable.restype = ctypes.c_double
    return lib

def get_general_admahls_plot(lib) -> go.Figure:
    ''' Generate a generalized plot for Amdahl's Law '''
    FP = np.array([0.5, 0.75, 0.9, 0.95])  # Fractions of the program that are parallelizable
    P = np.array([5, 10, 100, 1000, 10000])  # Scenarios for number of processors
    S_VALS = np.array([5, 10, 100, 1000, 10000])  # Speedup value scenarios to label
    COLOR_MAP = ['blue', 'orange', 'red', 'purple']  # Explicit color map for different speedup lines
    
    # Begin building the line graph plot
    fig = go.Figure()
    for f in FP:
        speedups = [lib.getAmdahlsLaw(f, p) for p in P]
        fig.add_trace(go.Scatter(
            x=P,  # fp on the x-axis
            y=speedups,  # Calculated speedup on the y-axis
            mode='lines+markers',  # Add lines and markers at known points
            name=f'fₚ={f}',  # Label each line
            line=dict(width=2, color=COLOR_MAP[f]),  # Line width and color
            marker=dict(size=6, color=COLOR_MAP[f])  # Marker size and color
        ))
        
    # Format the layout with title and axis titles
    fig.update_layout(
        title='Amdahl\'s Law: Speedup vs Number of Processors (Theoretical)',
        xaxis_title='Number of Processors (P)',
        yaxis_title='Speedup (Sₚ)',
        legend=dict(title='Parallel Fraction (fₚ)', x=0.01, y=0.99),
        template='seaborn',  # Cool template
    )
    
    # Add y-tick labels for specific speedup values
    fig.update_yaxes(tickmode='array', tickvals=S_VALS, ticktext=[str("S", s) for s in S_VALS])

    # Return the plot
    return fig

def add_cur_theoretical_to_fig(lib, fig: go.Figure, fp: float) -> go.Figure:
    ''' Add the current fP for the provided .c program to the theoretical Amdahl's Law plot '''
    P = np.array([5, 10, 100, 1000, 10000])  # Scenarios for number of processors
    S_VALS = np.array([5, 10, 100, 1000, 10000])  # Speedup value scenarios to label
    COLOR = 'green'  # Color for the current fP line
    
    # Add a line to the current plot
    speedups = [lib.getAmdahlsLaw(fp, p) for p in P]  # Calculate the theoretical speedup values
    fig.add_trace(go.Scatter(
        x=P,  # fp on the x-axis
        y=speedups,  # Calculated speedup on the y-axis
        name=f'Provided Program (fₚ={fp})',  # Label the line
        mode='lines+markers',  # Add lines and markers at known points
        line=dict(width=2, color=COLOR, dash='dash'),  # Line width and dashed style
        marker=dict(size=6, color=COLOR)  # Marker size and color
    ))
    
    return fig    

def get_num_cores() -> int:
    ''' Get the number of available CPU cores on the host machine '''
    cpu_count = os.cpu_count()
    return cpu_count if cpu_count is not None else 1  # Fallback to 1 if cpu_count() returns None

