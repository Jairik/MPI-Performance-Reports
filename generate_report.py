''' Main.py - Entry point for performance analysis, intaking the summation.c results and presenting it in meaningful ways. '''

import subprocess
import os
import ctypes
import numpy as np
import plotly.graph_objects as go

# Globally define the file path of the executable (assuming in the same directory)
c_file = 'summation.c'
executable = 'summation'

def compile_mpi_program() -> None:
    ''' Attempt to compile the globally defined MPI C program using mpicc '''
    try:
        subprocess.run(['mpicc', c_file, '-o', executable], check=True)
        print(f"Successfully compiled {c_file} to {executable} using mpicc.")  # Debugging statement for now
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        exit(1)

def run_executable(x: int = 10000000, np: int = 4) -> str:
    ''' Attempt to run the globally defined executable using mpirun with a specified number of processes and x parameter '''
    try:
        result = subprocess.run(['mpirun', '-np', f'{np}', f'./{executable}', f'{x}'], capture_output=True, text=True, check=True)
        print(result.stdout)  # Debugging: print the output
    except subprocess.CalledProcessError as e:
        print(f"Execution failed: {e}")
        exit(1)
    return result.stdout  # Return the output for further processing

def load_c_library(lib_path: str = "algorithmslib.so") -> ctypes.CDLL:
    ''' Load the C shared library for performance calculations '''
    lib = ctypes.CDLL(lib_path)
    # Declaring argument types
    lib.getSpeedup.argtypes = [ctypes.c_double, ctypes.c_double]
    lib.getEfficiency.argtypes = [ctypes.c_double, ctypes.c_int]
    lib.getAmdahlsLaw.argtypes = [ctypes.c_double, ctypes.c_double]
    # Declaring the return types
    lib.getSpeedup.restype = ctypes.c_double
    lib.getEfficiency.restype = ctypes.c_double
    lib.getAmdahlsLaw.restype = ctypes.c_double
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

def add_cur_theoretical(lib, fig: go.Figure, fp: float) -> go.Figure:
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

def get_speedup(lib, T1: float, Tp: float) -> float:
    ''' Wrapper function to get speedup from the C library '''
    return lib.getSpeedup(T1, Tp)

def get_efficiency(lib, T1: float, p: int) -> float:
    ''' Wrapper function to get efficiency from the C library '''
    return lib.getEfficiency(T1, p)

# NOT TO BE USED - WILL BE REPLACED BY ENDPOINTS AND WHATNOT
def main():
    # Compile the MPI C program
    compile_mpi_program()
    
    # Get the shared library
    lib = load_c_library()
    
    # Get the general Amdahl's Law plot
    amdahls_plot = get_general_admahls_plot(lib)
    amdahls_plot.show()
    
    