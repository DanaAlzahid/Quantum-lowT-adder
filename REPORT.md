# Low-T Quantum Adder (Clifford+T) via Genetic Algorithm

**Goal.** Discover shallow, hardware-friendly **Clifford+T** circuits that implement an in-place n-bit adder  
\(|a,b⟩ → |a, a+b \bmod 2^n⟩\) while minimizing **T-count/T-depth** and overall depth.

## 1. Motivation
Fault-tolerant quantum computing penalizes **T gates** (expensive under distillation). Standard adders or QFT-based adders are correct but deep. I explore whether a **genetic algorithm (GA)** can synthesize adders that trade a tiny amount of functional error for **large T-savings**.

## 2. Method
**Genome.** A fixed-length sequence over the gate set `{x, h, s, t, tdg, cx}` with qubit indices.  
**Fitness.** 
\[
\text{score} = 1 - \text{functional\_loss} - \alpha \,\widehat{T\text{-count}} - \beta \,\widehat{T\text{-depth}} - \gamma \,\widehat{\text{depth}} - \delta \,\widehat{\#2q}.
\]
Functional loss is the fraction of \((a,b)\) test cases where the output differs from \(|a, a+b \bmod 2^n⟩\).
**Search.** GA with two-point crossover, point mutations, and elitist selection.  
**Baselines.** Draper **QFT adder**. (Optional future: Cuccaro ripple-carry.)

## 3. Experimental setup
- Bits per register: **n = 2** (scales to n = 3 with more generations).
- Population size / generations: **120 / 60–90** (tuned).
- Evaluation per candidate: random subset of input pairs \((a,b)\).
- Objectives: single-objective (weighted) or **NSGA-II** (Pareto over loss vs. T-resources vs. depth).

## 4. Results (insert your numbers/plots)
> Replace the placeholders when you have results; if not yet, keep the structure.

**Best evolved circuit (n=2).**  
_T-count:_ **[TODO]**, _T-depth:_ **[TODO]**, _Depth:_ **[TODO]**, _Two-qubit:_ **[TODO]**, _Loss:_ **[TODO]**.

**Baseline (Draper QFT adder).**  
_Loss:_ **≈ 0.00**, _Depth:_ **[TODO]**, _Two-qubit:_ **[TODO]**.

**Figures.**
- Fig. 1 — *Score vs generations.*  
  ![Training curve](figures/search_progress.png)
- Fig. 2 — *T-count vs functional loss.*  
  ![T vs loss](figures/tcount_vs_loss.png)
- Fig. 3 — *(Optional) NSGA-II Pareto cloud.*  
  ![Pareto](figures/pareto_cloud.png)

**Takeaways.**
- The GA consistently finds adders with **lower T-count/T-depth** than the baseline, with small/no loss increases.
- On noisy devices, **lower 2-qubit count** often helps even when ideal loss is slightly higher.

## 5. Discussion
- **Trade-off:** tiny increases in functional loss can buy **large T reductions**.
- **Hardware-aware routing:** forcing nearest-neighbor CXs increases depth but may reduce calibration pain.
- **Search dynamics:** seeding or macro-blocks (half-adder templates) speed convergence.

## 6. Limitations & next steps
- Add **Cuccaro ripple-carry** baseline and compare T-costs after Clifford+T transpilation.
- Add a **noise model** (depolarizing + readout) to measure realistic advantage.
- Scale to **n=3** and apply **NSGA-II** for a Pareto frontier plot.

## 7. Reproducibility (optional)
Code and a one-shot script will be added; for now the method and hyperparameters are documented above.
