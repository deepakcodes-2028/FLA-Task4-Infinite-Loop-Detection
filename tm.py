"""A compact deterministic single-tape Turing-machine simulator for FLA examples."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class TMResult:
    status: str
    steps: int
    state: str
    head: int
    tape: dict[int, str]
    reason: str
    cycle_length: int | None = None


def run_tm(
    transitions: dict[tuple[str, str], tuple[str, str, str]],
    input_text: str = "",
    *,
    start_state: str = "q0",
    halt_states: set[str] | None = None,
    blank: str = "_",
    max_steps: int = 500,
) -> TMResult:
    halt_states = halt_states or {"qhalt"}
    tape = {i: ch for i, ch in enumerate(input_text) if ch != blank}
    head, state, steps = 0, start_state, 0
    seen: dict[tuple[object, ...], int] = {}
    while steps < max_steps:
        if state in halt_states:
            return TMResult("HALTS", steps, state, head, tape, "Machine entered a designated halting state.")
        key = (state, head, tuple(sorted((i, s) for i, s in tape.items() if s != blank)))
        if key in seen:
            return TMResult("LOOPS", steps, state, head, tape, "The complete Turing-machine configuration repeated.", steps - seen[key])
        seen[key] = steps
        symbol = tape.get(head, blank)
        transition = transitions.get((state, symbol))
        if transition is None:
            return TMResult("HALTS", steps, state, head, tape, "No transition is defined for the current state and tape symbol.")
        next_state, write_symbol, direction = transition
        if write_symbol == blank:
            tape.pop(head, None)
        else:
            tape[head] = write_symbol
        if direction == "L":
            head -= 1
        elif direction == "R":
            head += 1
        elif direction != "S":
            raise ValueError("Direction must be L, R, or S.")
        state = next_state
        steps += 1
    return TMResult("UNKNOWN", steps, state, head, tape, f"Step limit ({max_steps}) reached without a halt or repeated configuration.")


def example_machines() -> dict[str, tuple[dict[tuple[str, str], tuple[str, str, str]], str, str]]:
    """Return small machines illustrating halt, cycle, and non-repeating growth."""
    return {
        "erase_and_halt": ({("q0", "1"): ("qhalt", "_", "R")}, "1", "q0"),
        "two_cell_oscillator": ({
            ("q0", "1"): ("q1", "1", "R"),
            ("q1", "_"): ("q0", "_", "L"),
        }, "1", "q0"),
        "right_writer": ({
            ("q0", "_"): ("q0", "1", "R"),
            ("q0", "1"): ("q0", "1", "R"),
        }, "", "q0"),
    }
