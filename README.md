# Low‑T Quantum Adder (Clifford+T) via GA — Baseline & Pareto Mode

This project evolves **Clifford+T** circuits that implement an in‑place n‑bit adder |a,b⟩→|a, a+b (mod 2^n)⟩ while *minimizing* **T‑count/T‑depth** and overall resources.

## Features
- Genetic Algorithm over {x, h, s, t, tdg, cx}
- Metrics: functional loss, T‑count, T‑depth, depth, and 2‑qubit count
- Baseline: **Draper QFT adder** for reference
- Optional **NSGA‑II** Pareto search for trade‑off frontiers

## Quickstart
1. Install deps:
   ```bash
   pip install qiskit deap numpy matplotlib
   ```
2. Open the notebook `low_t_adder_ga.ipynb` and run all cells.
3. Start with `N_BITS=2`, then try 3 with higher `POP_SIZE` and `N_GEN`.

## Deliverables
- Best circuit + metrics; baseline metrics
- Plots: search curve, T‑count vs loss, Pareto cloud (if enabled)
- Write‑up on trade‑offs and design choices

## Notes
- Set `NEAREST_NEIGHBOR=True` to force hardware‑friendly routing.
- Toggle `USE_NSGA2` to switch between single‑objective and Pareto search.
