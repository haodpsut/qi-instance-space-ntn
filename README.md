# qi-instance-space-ntn

Instance space analysis for quantum-inspired resource allocation in non-terrestrial networks.
Artefact for a short paper submitted to **QAI-SAGIN @ EAI AICON 2026**.

## What is here

| path | what |
|---|---|
| `code/e1_protocol.py` | the experiment: both arms under one protocol |
| `code/spike_qi_on_multimodal.py` | objective, instance generator and the four optimisers |
| `results/e1_protocol.json` | every per-seed result, 434 kB, the single source of truth |
| `figures/make_figures.py` | generates every figure, table and number in the paper |
| `paper/main.tex` | the paper, Springer LNICST (`llncs`) |

## Reproducing

```bash
python3 -m pip install numpy scipy cmaes matplotlib
OMP_NUM_THREADS=1 QIB_SEEDS=30 QIB_BUDGET=20000 QIB_WORKERS=40 python3 code/e1_protocol.py
python3 figures/make_figures.py
cd paper && pdflatex main.tex && pdflatex main.tex
```

The run took under ten minutes on 40 cores. `OMP_NUM_THREADS=1` matters: without it each worker
opens as many BLAS threads as there are cores and the pool runs slower than sequential code.

## What the protocol enforces

1. **Budget counted inside the objective**, not estimated from iteration counts, so the budget is
   enforced rather than assumed.
2. **Unit of analysis declared** as (configuration, instance), with seeds as repetitions inside a
   unit. Treating each seed as an independent observation inflates significance.
3. **Three categories excluded from the multimodality count** and reported rather than dropped:
   non-finite objectives, non-converged runs, and optima separated by less than the stated
   threshold.
4. **Every number in the paper is generated** from `results/e1_protocol.json`. No result number is
   typed into the LaTeX source.

## Scope

One allocation problem, one instance generator. The protocol transfers; the verdict does not.
