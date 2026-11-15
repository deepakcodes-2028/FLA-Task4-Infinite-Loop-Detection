# Assignment 4 alignment

The CLA-2 Task 4 brief asks the team to select a real-world problem (including infinite-loop detection), formulate the decision problem, apply Turing-machine/computability concepts, explain decidability, distinguish recognisability where applicable, provide a formal model and worked example, and propose a restricted practical solution. It also asks for a real-world/formal-model mapping, individual contributions, and presentation/reproducibility evidence.

| Assignment expectation | Where LoopScope addresses it |
|---|---|
| Define the software problem and assumptions | `docs/formal_model.md`, report Chapters 1-2 |
| Formal computational model | `HALT_TM`, `LOOP_TM`, `TOTAL_TM`, and mapping table |
| Decidability and recognisability analysis | Diagonal proof and complement argument in Chapter 3 |
| Restricted-case engineering approach | Static proof stage and deterministic interpreter |
| At least one worked example | `examples/`, benchmark explanations, report Chapter 5 |
| Diagram/table connecting real and formal views | Formal mapping table and diagrams under `docs/diagrams/` |
| Practical implications | Timeout comparison, fixed-width semantics, limitations |
| Team contribution statements | `CONTRIBUTIONS.md` and report Chapter 9 |
| Validation and evidence | 15-program benchmark, 2,400-case sweep, test suite, CSVs, and charts |

The report should be reviewed by all team members before submission. The contribution table is a proposed role split and must be edited if the actual division of work differs.
