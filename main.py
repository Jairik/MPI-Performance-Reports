'''
Holds the following endpoints
    cores: '/api/cores', - Number of available cores on the host computer
    graph: '/api/graph', - Pure HTML embedding of graph
    questions: '/api/analysis', - Analysis stats for each core
'''

from flask import Flask, Response  # Defining endpoints
import generate_report as gp  # Importing generate_report module to access its functions

app = Flask(__name__)  # Instantiate the app

# Compile the MPI C program
gp.compile_mpi_program()

# Get the shared library
lib = gp.load_c_library()

@app.get('/api/cores')
def get_cores():
    ''' Get the number of available CPU cores on the host machine '''
    num_cores = int(gp.get_num_cores())
    return {'cores': num_cores}
    
@app.post('/api/graph')
def get_graph():
    ''' Get the HTML embedding of the Amdahl's Law graph and return as pure HTML '''
    lib = gp.load_c_library()
    fig = gp.get_general_admahls_plot(lib)
    html_graph = fig.to_html(full_html=False)
    return Response(html_graph, mimetype='text/html')

@app.post('/api/analysis')
def get_analysis():
    ''' Get analysis stats for each core '''
    # TODO

if __name__ == "__main__":
    app.run()
