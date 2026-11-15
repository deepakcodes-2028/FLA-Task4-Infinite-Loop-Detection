# LoopScope – Infinite-Loop Detection in Software

### Course: 21CSC301T – Formal Language and Automata
**Assessment:** CLA-2 – Assessment Task 4 (Team Work)

**Selected Problem:** Infinite-Loop Detection in Software

**Institution:** SRM Institute of Science and Technology, Tiruchirappalli

---

## Project Overview

**LoopScope** is an original Python-based educational prototype that demonstrates the boundary between the undecidable general Halting Problem and restricted program analyses that can provide sound answers.

The application accepts programs written in a small Python-like language called **MiniLoop** and analyses whether a program terminates or continues indefinitely.

The tool produces one of three possible outcomes:

| Outcome | Description |
|---|---|
| `HALTS` | A supported static proof or completed execution establishes termination. |
| `LOOPS` | A supported static argument or repeated deterministic machine configuration establishes nontermination. |
| `UNKNOWN` | The implemented analysis rules cannot prove either result within the execution budget. |

LoopScope deliberately does not claim to decide arbitrary programs. Its static analysis handles selected single-counter loops, while its runtime analysis handles finite executions and repeated machine configurations.

A growing state that never repeats may remain `UNKNOWN`.

## Features

1. **MiniLoop Parser and Compiler:** Supports assignments, integer arithmetic, `while`, `if/else`, `break`, and `pass`.
2. **Static Termination Analysis:** Provides proofs using monotone ranking functions, recurrent counter conditions, constant-step `!=` reachability, and simple constant guards.
3. **Configuration-Cycle Detection:** Executes a deterministic register machine and detects repeated complete configurations.
4. **Fixed-Width Register Mode:** Supports unsigned registers from 1 to 32 bits to demonstrate finite-state computation.
5. **Turing Machine Simulator:** Includes a separate deterministic single-tape Turing machine simulator.
6. **Diagonalisation Demonstration:** Provides a finite meta-level demonstration of why each total candidate decider is contradicted by an inverted self-input result.
7. **Benchmarking and Experiments:** Includes a 15-program benchmark, 2,400 generated linear-loop cases, CSV exports, and Matplotlib charts.

## Technologies Used

- **Programming Language:** Python 3.10+
- **Testing Framework:** Pytest
- **Data Analysis and Visualisation:** Matplotlib
- **
