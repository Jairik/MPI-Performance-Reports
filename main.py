'''
Holds the following endpoints
    cores: '/api/cores', - Number of available cores on the host computer
    graph: '/api/graph', - Pure HTML embedding of graph
    questions: '/api/analysis', - Analysis stats for each core
'''

from flask import Flask, Response  # Defining endpoints
import general_utils as gp  # Importing defined utils

app = Flask(__name__)  # Instantiate the app

# Compile the MPI C program
gp.compile_mpi_program()

# Get the shared library
lib = gp.load_c_library()

@app.get('/api/cores')
def get_cores() -> dict:
    ''' Get the number of available CPU cores on the host machine '''
    num_cores = int(gp.get_num_cores())  # Get number of cores from generate_report module
    return {'cores': num_cores}  # Return as JSON response
    
@app.post('/api/graph')
def get_graph() -> Response:
    ''' Get the HTML embedding of the Amdahl's Law graph and return as pure HTML '''
    fig = gp.get_general_admahls_plot(lib)
    html_graph = fig.to_html(full_html=False)  # Convert the plot to HTML format
    return Response(html_graph, mimetype='text/html')  # Return as HTML response

@app.post('/api/analysis')
def get_analysis(filename: str = 'summation.c', x: int = 10000000, np: int = 4) -> dict:
    ''' Get analysis stats execution on each core '''
    # TODO

if __name__ == "__main__":
    app.run()
