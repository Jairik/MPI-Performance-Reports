# Performance Analysis on MPI Program using Amdahl's Law

Generates autonomous performance analysis reports of the summation program using Amdahl's Law.
Expandable to analyze any MPI program with certain print outputs. Viewable via localhost web interface. 

## To run:

```bash
# Make and activate a python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install uv  # Tool to install dependencies significantly faster
uv pip install -r requirements.txt
# Run the program
python main.py
```

Then, the site should be viewable on `http://127.0.0.1:5000/`.

## Troubleshooting
If there are errors regarding C shared libraries, run:
```bash
# from the folder containing algorithmslib.c
gcc -O3 -fPIC -shared algorithmslib.c -o algorithmslib.so
```