
# Quick runner to produce results into ./results
from ga_core import *

# Speed-friendly defaults
POP_SIZE=80
N_GEN=40
N_BITS=2
EXHAUSTIVE_VERIFY=True

pop, progress, best = run_search()
path = export_all(pop, progress, best, results_dir="results", save_plots=True)
print("Saved results to:", path)
