"""Executable finite meta-demonstration of the diagonal contradiction."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    name: str
    predict: str
    actual_diagonal_behaviour: str
    is_wrong: bool
    explanation: str


def _candidate_predictions() -> list[tuple[str, str]]:
    # Each candidate is a total, terminating guesser over the abstract self-input.
    return [
        ("always_halts", "HALTS"),
        ("always_loops", "LOOPS"),
        ("source_keyword_rule", "HALTS"),
        ("fixed_timeout_guess", "LOOPS"),
    ]


def diagonal_demo() -> list[Candidate]:
    """Invert each candidate's prediction, as the diagonal construction requires.

    This function demonstrates the logical contradiction at the meta-level. It does
    not claim to construct a physical Python object capable of encoding its own source.
    """
    results: list[Candidate] = []
    for name, prediction in _candidate_predictions():
        actual = "LOOPS" if prediction == "HALTS" else "HALTS"
        results.append(Candidate(
            name=name,
            predict=prediction,
            actual_diagonal_behaviour=actual,
            is_wrong=(prediction != actual),
            explanation=("The diagonal program loops when predicted to halt." if actual == "LOOPS"
                         else "The diagonal program halts when predicted to loop."),
        ))
    return results
