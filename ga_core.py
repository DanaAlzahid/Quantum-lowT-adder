
import math, random, itertools, numpy as np, matplotlib.pyplot as plt, json, os
from deap import base, creator, tools, algorithms
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.circuit.library import QFT

random.seed(42); np.random.seed(42)

# --- Config (can be overridden by quickrun) ---
N_BITS   = 2
N_QUBITS = 2 * N_BITS
MAX_GATES = 40
POP_SIZE  = 120
N_GEN     = 60
P_CX      = 0.7
P_MUT     = 0.3
MUT_INDPB = 0.08
N_SAMPLES = min(16, 2**(2*N_BITS))
EXHAUSTIVE_VERIFY = (N_BITS <= 2)
NEAREST_NEIGHBOR = False
USE_NSGA2 = True  # Pareto mode

# --- Gate set & genome ---
GATE_X, GATE_H, GATE_S, GATE_T, GATE_TDG, GATE_CX = range(6)

def random_gene():
    gt = random.randrange(6)
    q1 = random.randrange(N_QUBITS)
    q2 = q1
    if gt == GATE_CX:
        q2 = random.randrange(N_QUBITS)
        while q2 == q1 or (NEAREST_NEIGHBOR and abs(q1-q2) != 1):
            q1 = random.randrange(N_QUBITS); q2 = random.randrange(N_QUBITS)
    return (gt, q1, q2)

def mutate_gene(g):
    gt, q1, q2 = g
    which = random.randrange(3)
    if which == 0:
        gt = random.randrange(6); 
        if gt != GATE_CX: q2 = q1
    elif which == 1:
        q1 = random.randrange(N_QUBITS); 
        if gt != GATE_CX: q2 = q1
    else:
        if gt == GATE_CX:
            q2 = random.randrange(N_QUBITS)
            if q2 == q1: q2 = (q1 + 1) % N_QUBITS
            if NEAREST_NEIGHBOR and abs(q1-q2) != 1:
                q2 = q1 + 1 if q1+1 < N_QUBITS else q1-1
        else:
            q2 = q1
    return (gt, q1, q2)

def build_circuit(genome):
    qc = QuantumCircuit(N_QUBITS, name="cand")
    for (gt, q1, q2) in genome:
        if gt == GATE_X:     qc.x(q1)
        elif gt == GATE_H:   qc.h(q1)
        elif gt == GATE_S:   qc.s(q1)
        elif gt == GATE_T:   qc.t(q1)
        elif gt == GATE_TDG: qc.tdg(q1)
        elif gt == GATE_CX:
            if q1 != q2 and (not NEAREST_NEIGHBOR or abs(q1 - q2) == 1):
                qc.cx(q1, q2)
    return qc

# --- Metrics & loss ---
def t_metrics(qc):
    tcnt = 0; tdepth=0; in_layer=False
    for inst,_,_ in qc.data:
        if inst.name in ('t','tdg'):
            tcnt += 1
            if not in_layer: tdepth += 1; in_layer=True
        else:
            in_layer=False
    return tcnt, tdepth

def twoq_count(qc):
    return sum(1 for inst,_,_ in qc.data if inst.num_qubits >= 2)

def circuit_depth(qc):
    d = qc.depth()
    return int(d) if d is not None else 0

def prepare_basis_state(a, b, nbits):
    qc = QuantumCircuit(2*nbits)
    for i in range(nbits):
        if (a>>i)&1: qc.x(i)
        if (b>>i)&1: qc.x(nbits+i)
    return qc

def read_regs(msb_to_lsb, nbits):
    s = msb_to_lsb[::-1]
    out_a = int(s[:nbits][::-1], 2)
    out_b = int(s[nbits:2*nbits][::-1], 2)
    return out_a, out_b

def adder_loss(qc, nbits, samples):
    errs = 0
    universe = list(itertools.product(range(2**nbits), repeat=2))
    random.shuffle(universe)
    for k in range(min(samples, len(universe))):
        a, b = universe[k]
        sv = Statevector.from_label('0'*(2*nbits))
        sv = sv.evolve(prepare_basis_state(a,b,nbits)).evolve(qc)
        meas, p = max(sv.probabilities_dict().items(), key=lambda kv: kv[1])
        out_a, out_b = read_regs(meas, nbits)
        if out_a != a or out_b != ((a+b) % (2**nbits)):
            errs += 1
    return errs / max(1, min(samples, len(universe)))

def evaluate_candidate(genome):
    qc = build_circuit(genome)
    loss = adder_loss(qc, N_BITS, N_SAMPLES)
    tcnt, tdep = t_metrics(qc)
    dpth = circuit_depth(qc)
    n2q  = twoq_count(qc)
    tcnt_norm = tcnt / max(1, MAX_GATES)
    tdep_norm = tdep / max(1, MAX_GATES//4)
    dpth_norm = dpth / max(1, MAX_GATES)
    n2q_norm  = n2q  / max(1, MAX_GATES//2)
    score = 1 - loss - 0.30*tcnt_norm - 0.25*tdep_norm - 0.20*dpth_norm - 0.15*n2q_norm
    return score, loss, tcnt, tdep, dpth, n2q, qc

# Baseline: Draper QFT adder
def draper_qft_adder(nbits):
    qc = QuantumCircuit(2*nbits, name="draper_adder")
    a = list(range(nbits))
    b = list(range(nbits, 2*nbits))
    qc.append(QFT(nbits, do_swaps=True).to_instruction(), b)
    for i, qa in enumerate(a):
        for j, qb in enumerate(b):
            k = j - i
            if k >= 0:
                theta = math.pi / (2**k)
                qc.cp(theta, qa, qb)
    qc.append(QFT(nbits, do_swaps=True, inverse=True).to_instruction(), b)
    return qc

def run_search():
    if USE_NSGA2:
        creator.create("FitnessMin3", base.Fitness, weights=(-1.0,-1.0,-1.0))
        creator.create("Individual", list, fitness=creator.FitnessMin3)
    else:
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
    toolbox = base.Toolbox()
    toolbox.register("gene", random_gene)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.gene, n=MAX_GATES)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    def mut_ind(individual, indpb=MUT_INDPB):
        for i in range(len(individual)):
            if random.random() < indpb:
                individual[i] = mutate_gene(individual[i])
        return (individual,)
    def eval_SO(individual):
        s, *_ = evaluate_candidate(individual)
        return (s,)
    def eval_MO(individual):
        _, loss, tcnt, tdep, dpth, n2q, _ = evaluate_candidate(individual)
        tcnt_norm = tcnt / max(1, MAX_GATES)
        n2q_norm  = n2q  / max(1, MAX_GATES//2)
        dpth_norm = dpth / max(1, MAX_GATES)
        return (loss, tcnt_norm + 0.5*n2q_norm, dpth_norm)
    if USE_NSGA2:
        toolbox.register("evaluate", eval_MO)
        toolbox.register("select", tools.selNSGA2)
    else:
        toolbox.register("evaluate", eval_SO)
        toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", mut_ind, indpb=MUT_INDPB)
    pop = toolbox.population(n=POP_SIZE)
    if USE_NSGA2:
        pop = tools.selNSGA2(pop, k=len(pop))
    progress = []
    for gen in range(N_GEN):
        offspring = algorithms.varAnd(pop, toolbox, cxpb=P_CX, mutpb=P_MUT)
        fits = list(map(toolbox.evaluate, offspring))
        for ind, fit in zip(offspring, fits):
            ind.fitness.values = fit
        pop = toolbox.select(offspring, k=len(pop))
        if USE_NSGA2:
            def composite(ind):
                loss, reg, dep = ind.fitness.values
                return 1 - loss - 0.4*reg - 0.3*dep
            progress.append(max(map(composite, pop)))
        else:
            progress.append(max(ind.fitness.values[0] for ind in pop))
    # Representative best
    best = min(pop, key=lambda ind: (ind.fitness.values[0], ind.fitness.values[1])) if USE_NSGA2 else max(pop, key=lambda ind: ind.fitness.values[0])
    b_score, b_loss, b_tcnt, b_tdep, b_depth, b_n2q, b_qc = evaluate_candidate(best)
    return pop, progress, (b_score, b_loss, b_tcnt, b_tdep, b_depth, b_n2q, b_qc)

def export_all(pop, progress, best_info, results_dir=\"results\", save_plots=True):
    os.makedirs(results_dir, exist_ok=True)
    b_score, b_loss, b_tcnt, b_tdep, b_depth, b_n2q, b_qc = best_info
    # Save metrics
    metrics = {
        \"best\": {\"score\": b_score, \"loss\": b_loss, \"T_count\": b_tcnt, \"T_depth\": b_tdep, \"depth\": b_depth, \"two_qubit\": b_n2q},
        \"config\": {\"N_BITS\": N_BITS, \"POP_SIZE\": POP_SIZE, \"N_GEN\": N_GEN, \"USE_NSGA2\": USE_NSGA2, \"NEAREST_NEIGHBOR\": NEAREST_NEIGHBOR}
    }
    with open(os.path.join(results_dir, \"metrics.json\"), \"w\") as f: json.dump(metrics, f, indent=2)
    # Save baseline metrics
    base = draper_qft_adder(N_BITS)
    base_loss = adder_loss(base, N_BITS, samples=min(32, 2**(2*N_BITS)))
    base_m = {\"loss\": base_loss, \"depth\": int(base.depth()), \"two_qubit\": int(sum(1 for g,_,_ in base.data if g.num_qubits>=2))}
    with open(os.path.join(results_dir, \"baseline.json\"), \"w\") as f: json.dump(base_m, f, indent=2)
    # Save circuit text & qasm
    with open(os.path.join(results_dir, \"best_circuit.txt\"), \"w\") as f: f.write(b_qc.draw(output=\"text\").single_string())
    with open(os.path.join(results_dir, \"best_circuit.qasm\"), \"w\") as f: f.write(b_qc.qasm())
    # Plots
    if save_plots:
        plt.figure(); plt.title(\"Search progress\"); plt.plot(progress); plt.xlabel(\"Generation\"); plt.ylabel(\"Quality\"); plt.savefig(os.path.join(results_dir, \"search_progress.png\")); plt.close()
        xs, ys = [], []
        for ind in pop[:min(60, len(pop))]:
            _, loss, tcnt, _, _, _, _ = evaluate_candidate(ind)
            xs.append(tcnt); ys.append(loss)
        plt.figure(); plt.title(\"T-count vs functional loss\"); plt.scatter(xs, ys); plt.xlabel(\"T-count\"); plt.ylabel(\"Loss\"); plt.savefig(os.path.join(results_dir, \"tcount_vs_loss.png\")); plt.close()
        if USE_NSGA2:
            L = [ind.fitness.values[0] for ind in pop]
            R = [ind.fitness.values[1] for ind in pop]
            plt.figure(); plt.title(\"Pareto cloud: Loss vs T/2q regularizer\"); plt.scatter(R, L); plt.xlabel(\"T/2q regularizer\"); plt.ylabel(\"Loss\"); plt.savefig(os.path.join(results_dir, \"pareto_cloud.png\")); plt.close()
    return os.path.abspath(results_dir)
