''' Holds the Flask app endpoints to populate the frontend
        systemCores: '/api/cores',
        analysis: '/api/analysis'
'''

from flask import Flask, Response, send_file, request  # Defining endpoints
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

@app.post('/api/analysis')
def get_analysis() -> dict:
    ''' Get analysis stats execution on each core '''
    # Extract parameters from JSON body
    data = request.get_json() or {}
    filename = data.get('filename', 'summation.c')
    x = int(data.get('x', 1000000000))
    numP = data.get('numP', [1, 2, 8])
    
    gp.compile_mpi_program(filename)  # Try to compile the provided MPI C program
    response: dict = {}  # Initialize response dictionary
    serial_runtime: float = None  # Initialize serial runtime variable
    print(f"DEBUGGING: Received request - filename: {filename}, x: {x}, numP: {numP}")  # Debug: print the received parameters
    # Ensure 1 is the first element of numP (move it if present, or add it if missing)
    if 1 in numP:
        numP = [1] + [p for p in numP if p != 1]
    else:
        numP = [1] + list(numP)
    # Loop through each number of processes provided and append the results to the response
    last_graph_html = None  # Store the last graph HTML to add to top-level response
    for np in numP:
        result = gp.run_executable(lib, x, np)  # Run the compiled executable
        analysis_results: dict = gp.parse_execution_output(lib=lib, output=result, np=np, serial_time=serial_runtime)  # Parse the output into a dictionary
        print(f"Analysis results for {np} processes: {analysis_results}")  # Debug: print the analysis results
        if np == 1:  # Store the serial runtime for reference
            serial_runtime = analysis_results.get('serial', None)  # Store the serial runtime
        fig = gp.get_general_admahls_plot(lib)  # Get the general Amdahl's Law plot
        updated_fig = gp.add_cur_theoretical_to_fig(lib, fig, analysis_results['fp'])  # Add the analysis point to the plot
        graph_html = updated_fig.to_html(full_html=False, include_plotlyjs='cdn')  # Convert graph to HTML
        analysis_results['graph'] = graph_html  # Add the updated graph as HTML to the results
        last_graph_html = graph_html  # Store for top-level response
        response.setdefault('analyses', []).append({'num_processes': np, **analysis_results})  # Add the analysis results to the response object keyed by number of processes
    
    # Add the last graph to the top-level response for easy access
    if last_graph_html:
        response['graph'] = last_graph_html
    
    return response

if __name__ == "__main__":
    app.run()  # Startup the endpoints
