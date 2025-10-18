''' Helper functions for performance analysis '''

from pathlib import Path
import subprocess
import os
import ctypes
import numpy as np
import plotly.graph_objects as go

executable: str = str('summation')  # Default value, make sure python knows that it's a string

def compile_mpi_program(filename: str = 'summation.c') -> None:
    ''' Attempt to compile the globally defined MPI C program using mpicc '''
    global executable  # Use the global executable variable, not the local one
    executable = filename.replace('.c', '')  # Derive executable name from filename
    try:
        subprocess.run(['mpicc', filename, '-o', executable], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        exit(1)

def run_executable(lib, x: int = 50000, np: int = 4) -> str:
    ''' Attempt to run the globally defined executable using mpirun with a specified number of processes and x parameter '''
    cmd = ["mpirun", '--use-hwthread-cpus', "-np", str(np), f"./{executable}", str(x)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        # Show both stdout and stderr to see OpenMPI’s error
        msg = (
            f"Command failed: {' '.join(cmd)}\n"
            f"Exit code: {e.returncode}\n\n"
            f"--- STDOUT ---\n{e.stdout}\n"
            f"--- STDERR ---\n{e.stderr}\n"
        )
        raise RuntimeError(msg)
    return result.stdout  # Return the output for further processing

def parse_execution_output(lib, output: str, np: int, serial_time: float = None) -> dict:
    ''' Parse the output from the C program execution assign everything to a dictionary '''
    lines: list[str] = output.strip().split('\n')  # Split output into lines
    results: dict = {}  # Initialize results dictionary
    for line in lines:
        line = line.lower()
        # Extract run time values
        if "time" in line:
            # Extract per-core information for parallel programs
            if "mpi" in line:
                parts = line.split()  # Split line into parts by spaces
                rank = int(parts[5])  # Extract rank number, which should be at index 5
                time = float(parts[-1])  # Extract time value, which should be last
                results[f'rank {rank}'] = time  # Store in dictionary with rank as key
            # Extract serial information by seperate key
            elif "serial" in line:
                parts = line.split()  # Split line into parts by spaces
                time = float(parts[-1])  # Extract time value, which should be last
                results['serial'] = time  # Store in dictionary with 'serial' as key
        # Extract total summation value
        elif "summation" in line:
            parts = line.split()  # Split line into parts by spaces
            total = int(parts[-1])  # Extract total summation value, which should be last
            results['total'] = total  # Store in dictionary with 'total' as key
    
    add_all_stats_to_results(lib, results, np, serial_time)  # Add speedup, efficiency, and fraction parallel/serial to results (apply directly by reference)
    
    # Return the sorted results dictionary
    return dict(sorted(results.items(), key=lambda x: (isinstance(x[0], int), x[0])))

def add_all_stats_to_results(lib, results: dict, np: int, serial_time: float = None) -> None:
    ''' Derive the fraction of parallelizable code, speedup, and efficiency from the execution results '''
    # First (serial) pass reports serial metrics only
    if serial_time is None:
        results.setdefault("speedup", 1.0)
        results.setdefault("efficiency", 1.0)
        results.setdefault("fp", 0.0)
        results["fs"] = round(1.0 - results["fp"], 6)
        return

    # Collect per-rank times
    parallel_times = [
        v for k, v in results.items()
        if (isinstance(k, str) and k.lower().startswith("rank")) and isinstance(v, (int, float))
    ]
    # Fallback if nothing parsed for ranks add default values
    if not parallel_times:
        results["speedup"] = 1.0
        results["efficiency"] = 1.0
        results["fp"] = 0.0
        results["fs"] = 1.0
        return

    Tp = max(parallel_times)  # Get the maximum parallel time across all ranks
    # Fallback
    if Tp <= 0:
        results["speedup"] = 1.0
        results["efficiency"] = 1.0
        results["fp"] = 0.0
        results["fs"] = 1.0
        return

    # Calculate speedup, efficiency, and fraction parallelizable using the defined C library functions
    S = float(lib.getSpeedup(float(serial_time), float(Tp)))
    E = float(lib.getEfficiency(S, int(np)))
    fp = float(lib.getFractionParallelizable(float(serial_time), float(Tp), int(np)))

    # Assign rounded values to results dictionary
    results["speedup"] = round(S, 6)
    results["efficiency"] = round(E, 6)
    results["fp"] = round(max(0.0, min(1.0, fp)), 6)
    results["fs"] = round(1.0 - results["fp"], 6)

def load_c_library(lib_path: str = "algorithmslib.so") -> ctypes.CDLL:
    ''' Load the C shared library for performance calculations '''
    # Get the path to the shared library
    here = Path(__file__).resolve().parent
    lib_path1 = here / lib_path
    # Load the shared library
    lib = ctypes.CDLL(str(lib_path1))
    # Declaring argument types
    lib.getSpeedup.argtypes = [ctypes.c_double, ctypes.c_double]
    lib.getEfficiency.argtypes = [ctypes.c_double, ctypes.c_int]
    lib.getAmdahlsLaw.argtypes = [ctypes.c_double, ctypes.c_int]
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

    # Use logspace so that the processor counts scale smoothly from 1 → 10,000
    P = np.logspace(0, 4, num=80, base=10).astype(int)  # Scenarios for number of processors (log scale)
    S_VALS = np.array([5, 10, 100, 1000, 10000])  # Speedup value scenarios to label
    COLOR_MAP = ['blue', 'orange', 'red', 'purple']  # Explicit color map for different speedup lines
    
    # Begin building the line graph plot
    fig = go.Figure()
    for i, f in enumerate(FP):
        # Compute theoretical speedups based on Amdahl's Law for each processor count
        speedups = [lib.getAmdahlsLaw(float(f), int(p)) for p in P]

        # Add a trace (line) for each parallel fraction fₚ
        fig.add_trace(go.Scatter(
            x=P,  # fp on the x-axis (number of processors)
            y=speedups,  # Calculated speedup on the y-axis
            mode='lines+markers',  # Add lines and markers at known points
            name=f'fₚ={f}',  # Label each line
            line=dict(width=2, color=COLOR_MAP[i % len(COLOR_MAP)]),  # Line width and color
            marker=dict(size=6, color=COLOR_MAP[i % len(COLOR_MAP)])  # Marker size and color
        ))

    # Format the layout with title and axis titles
    fig.update_layout(
        title="Amdahl's Law: Speedup vs Number of Processors (Theoretical)",
        xaxis=dict(
            title='Number of Processors (P)',
            type='log',  # Use a logarithmic scale for P (1,10,100,1000,10000)
            dtick=1,
            showgrid=True,
            gridcolor='rgba(255,255,255,0.08)',
        ),
        yaxis=dict(
            title='Speedup (Sₚ)',
            rangemode='tozero',
            showgrid=True,
            gridcolor='rgba(255,255,255,0.08)',
        ),
        legend=dict(
            title='Parallel Fraction (fₚ)',
            orientation='v',       # Vertical legend
            x=1.02,               # Place to the right of the plotting area
            xanchor='left',
            y=1,
            yanchor='top'
        ),
        template='plotly_dark',  # Cool template
        margin=dict(l=60, r=120, t=60, b=50),  # Ensure space for the legend on the right and readable margins
        hovermode='x unified',  # Unified hover label for better readability
        uirevision='keep'       # Preserve zoom and pan state when refreshing
    )

    # Add hover info for clarity
    fig.update_traces(
        hovertemplate='P=%{x}<br>Sₚ=%{y:.2f}<extra>%{fullData.name}</extra>'
    )

    # Add y-tick labels for specific speedup values (still optional)
    fig.update_yaxes(tickmode='array', tickvals=S_VALS, ticktext=[f"S{s}" for s in S_VALS])

    # Return the plot
    return fig


def add_cur_theoretical_to_fig(lib, fig: go.Figure, fp: float) -> go.Figure:
    ''' Add the current fₚ for the provided .c program to the theoretical Amdahl's Law plot '''
    
    # Use logspace so the processor counts scale smoothly from 1 → 10,000
    P = np.logspace(0, 4, num=80, base=10).astype(int)  # Scenarios for number of processors (log scale)
    S_VALS = np.array([5, 10, 100, 1000, 10000])  # Speedup value scenarios to label
    COLOR = 'limegreen'  # Color for the current fₚ line
    
    # Calculate speedups
    speedups = [lib.getAmdahlsLaw(float(fp), int(p)) for p in P]  # Calculate the theoretical speedup values
    
    # Add a trace (line) for the current program's fₚ
    fig.add_trace(go.Scatter(
        x=P,  # fp on the x-axis (number of processors)
        y=speedups,  # Calculated speedup on the y-axis
        name=f'Provided Program (fₚ={fp:.2f})',  # Label the line
        mode='lines+markers',  # Add lines and markers at known points
        line=dict(width=2, color=COLOR, dash='dash'),  # Line width and dashed style
        marker=dict(size=6, color=COLOR)  # Marker size and color
    ))
    
    # Improve hover clarity and scaling consistency with the main plot
    fig.update_traces(
        selector=dict(name=f'Provided Program (fₚ={fp:.2f})'),
        hovertemplate='P=%{x}<br>Sₚ=%{y:.2f}<extra>%{fullData.name}</extra>'
    )
    
    # Ensure axes and layout remain consistent after adding this trace
    fig.update_layout(
        xaxis=dict(type='log', dtick=1),  # Keep log scaling
        uirevision='keep'  # Preserve zoom and pan state when refreshing
    )
    
    return fig
 

def get_num_cores() -> int:
    ''' Get the number of available CPU cores on the host machine '''
    cpu_count = os.cpu_count()
    return cpu_count if cpu_count is not None else 8  # Default to 8 cores if undetectable

