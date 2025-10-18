'''
Holds the following endpoints
    systemCores: '/api/cores',
	reportsGraph: '/api/graph',
	analysis: '/api/analysis',
'''

from flask import Flask, Response, send_file  # Defining endpoints
import general_utils as gp  # Importing defined utils
import ctypes  # Prevent any type issues with C library
import plotly.graph_objects as go  # Prevent any issues with converting the plot to html

app = Flask(__name__)  # Instantiate the app

# Compile the MPI C program
gp.compile_mpi_program()

# Get the shared library
lib = gp.load_c_library()

@app.get('/')
def serve_index() -> Response:
    ''' Serve the index.html file as the main landing page '''
    return  send_file('index.html') # Return the index.html file when opening localhost

@app.get('/api/cores')
def get_cores() -> dict:
    ''' Get a list of available CPU cores on the host machine '''
    num_cores = int(gp.get_num_cores())  # Get number of cores from generate_report module
    return {'options': [{'cores': i} for i in range(1, num_cores+1)]}  # Return list as JSON response
    
@app.get('/api/graph')
def get_graph() -> Response:
    ''' Get the HTML embedding of the Amdahl's Law graph and return as pure HTML '''
    fig = gp.get_general_admahls_plot(lib)
    html_graph = fig.to_html(full_html=False)  # Convert the plot to HTML format
    return Response(html_graph, mimetype='text/html')  # Return as HTML response

@app.post('/api/analysis')
def get_analysis(filename: str = 'summation.c', x: int = 10000000, numP: list[int] = [1, 2, 8]) -> dict:
    ''' Get analysis stats execution on each core '''
    gp.compile_mpi_program(filename)  # Try to compile the provided MPI C program
    response: dict = {}  # Initialize response dictionary
    serial_runtime: float = None  # Initialize serial runtime variable
    # Ensure 1 is the first element of numP (move it if present, or add it if missing)
    if 1 in numP:
        numP = [1] + [p for p in numP if p != 1]
    else:
        numP = [1] + list(numP)
    # Loop through each number of processes provided and append the results to the response
    for np in numP:
        result = gp.run_executable(lib, x, np)  # Run the compiled executable
        analysis_results: dict = gp.parse_execution_output(lib=lib, output=result, np=np, serial_time=serial_runtime)  # Parse the output into a dictionary
        fig = gp.get_general_admahls_plot(lib)  # Get the general Amdahl's Law plot
        updated_fig = gp.add_analysis_point_to_plot(fig, analysis_results['fp'], analysis_results['speedup'], np)  # Add the analysis point to the plot
        analysis_results['graph'] = updated_fig.to_html(full_html=False)  # Add the updated graph as HTML to the results
        response.setdefault('analyses', []).append({'num_processes': np, **analysis_results})  # Add the analysis results to the response object keyed by number of processes
        # Store the serial runtime for reference
        if np == 1:
            serial_runtime = analysis_results.get('serial', None)  # Store the serial runtime
    
    return response

if __name__ == "__main__":
    app.run()  # Startup the endpoints
