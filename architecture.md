# LoopScope architecture

## Pipeline

1. **Parse and validate.** Python's AST parser reads MiniLoop source, but only a whitelist of statements and expressions is accepted. The implementation never calls Python `eval` or `exec`.
2. **Compile.** Assignments, conditional branches, loops, jumps, and halt are translated into a small register-machine instruction sequence.
3. **Static proof stage.** For one loop with a single counter update, the analyser checks a small set of ranking, recurrence, constant-guard, equality, and target-reachability rules.
4. **Concrete execution stage.** Programs not covered by the static rules run in a deterministic interpreter. The observed configuration contains the program counter and the complete variable store.
5. **Verdict.** The interface returns `HALTS`, `LOOPS`, or `UNKNOWN`, together with the reason, method, and execution evidence where applicable.

## MiniLoop language

The accepted statements are single-variable assignments, augmented arithmetic updates, `while`, `if/else`, `break`, and `pass`. Expressions include integer and Boolean constants, variable names, `+`, `-`, `*`, `//`, `%`, unary operators, comparisons, and Boolean `and/or`.

Imports, calls, attribute access, external input/output, and arbitrary Python constructs are rejected. This keeps the execution deterministic and prevents untrusted source from executing Python side effects.

## Static proof rules

| Rule | Pattern | Verdict | Proof idea |
|---|---|---|---|
| Ascending ranking | `while x <(=) b: x += d`, `d > 0` | HALTS | `b - x` decreases by a positive constant while the guard is true. |
| Descending ranking | `while x >(=) b: x -= d`, `d > 0` | HALTS | `x - b` decreases by a positive constant while the guard is true. |
| Recurrent counter | Inequality guard with update directed away from its exit boundary | LOOPS | The update preserves the guard indefinitely. |
| Constant-step `!=` | `while x != b: x += d` | HALTS or LOOPS | The target is reached exactly when `(b - x) / d` is a non-negative integer. |
| Stable guard | No update to the guarded variable | LOOPS when initially true | The state and true guard remain unchanged. |
| Literal guard | `while True` without `break`; or `while False` | LOOPS or HALTS | The guard alone determines entry and exit. |

The static rules deliberately require a one-loop, one-counter fragment. They do not attempt to infer arbitrary ranking functions.

## Configuration-cycle proof

For compiled instruction pointer `pc` and store `sigma`, a configuration is `(pc, sigma)`. The MiniLoop interpreter is deterministic. If the same complete configuration appears at two different steps, all future transitions from that configuration repeat, establishing an infinite cycle. A program with an ever-growing store may never repeat; if the step budget is reached, LoopScope reports `UNKNOWN`.

## Fixed-width mode

When enabled, each integer register is interpreted as an unsigned `k`-bit value and arithmetic writes wrap modulo `2^k`. A program with `m` registers and `p` instruction positions then has at most `p * 2^(k*m)` configurations. This makes exhaustive state exploration decidable in principle, although the state space may be very large. Fixed-width execution is a different semantic model from unbounded mathematical integers.
