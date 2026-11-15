# Formal model and computability analysis

## 1. Real-world question

Given a program `P` and a fixed input `w`, determine whether the execution of `P(w)` eventually stops or continues indefinitely. We assume deterministic execution for the machine model and treat the program plus its input as one computation.

## 2. Turing-machine formulation

A program can be represented by a Turing machine `M`, and the input is represented by the initial tape contents `w`. The relevant languages are:

- `HALT_TM = { <M,w> | M halts on input w }`.
- `LOOP_TM = { <M,w> | M does not halt on input w } = complement(HALT_TM)`.
- `TOTAL_TM = { <M> | M halts on every input }`.

The question “does this particular run hang?” is the membership question `<M,w> in LOOP_TM`. The question “does this program terminate for all inputs?” is expressed through `TOTAL_TM`.

| Software view | Computability view |
|---|---|
| Source program `P` | Encoded Turing machine `M_P` |
| Chosen input `w` | Initial tape contents `w` |
| Execution of `P(w)` | Sequence of instantaneous descriptions of `M_P` |
| Program returns | Machine enters a halting state |
| Program runs forever | Machine never enters a halting state |
| General loop detector | A decider for `LOOP_TM` |

## 3. Why a universal exact detector cannot exist

Assume, for contradiction, that a total algorithm `H` decides whether any encoded machine halts on a supplied input. Construct a machine `D` that receives an encoding `<M>` and asks `H` about `<M,<M>>`. If `H` predicts that `M` halts on its own encoding, `D` deliberately runs forever. If `H` predicts that `M` does not halt on its own encoding, `D` halts immediately.

Now provide `<D>` as input to `D`. If `H` says that `D(<D>)` halts, the definition makes it loop. If `H` says that it loops, the definition makes it halt. Both possibilities contradict the assumed correctness of `H`. Therefore no general halting decider exists. Since a decider for `LOOP_TM` would also decide its complement `HALT_TM`, `LOOP_TM` is undecidable as well.

## 4. Recognisability is asymmetric

`HALT_TM` is Turing-recognisable: simulate `M(w)` and accept once a halting configuration is observed. On a non-halting run, the simulation may continue forever, which is allowed for a recogniser.

`LOOP_TM` is not Turing-recognisable. If both `HALT_TM` and its complement were recognisable, dovetailing their recognisers would decide `HALT_TM`, contradicting the diagonal proof. This is why observing a completed run is definitive, while a long-running computation cannot in general be certified as an infinite loop by waiting alone.

A language is decidable exactly when it and its complement are both Turing-recognisable. Rice's theorem further establishes that every non-trivial semantic property of the partial function computed by a program is undecidable; examples include total termination and equivalence of computed functions [4]. The diagonal proof above is sufficient for the specific halting question studied here.

## 5. Practical consequence

A useful engineering tool must restrict its program class, use bounded abstractions, or return an inconclusive result. LoopScope follows this principle: it provides explicit proof rules for a small fragment, explores deterministic machine configurations when needed, and returns `UNKNOWN` when the evidence is insufficient. It never interprets a timeout as a mathematical proof of nontermination.
