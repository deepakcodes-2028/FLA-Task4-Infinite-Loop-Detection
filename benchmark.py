"""Small reproducible benchmark; expected outcomes are independently hand-analysed."""
from __future__ import annotations

from dataclasses import dataclass
from .analyzer import analyze
from .language import compile_source
from .runtime import execute


@dataclass(frozen=True)
class BenchmarkProgram:
    name: str
    category: str
    source: str
    expected: str
    note: str


BENCHMARK: list[BenchmarkProgram] = [
    BenchmarkProgram("countdown", "ranking", "i = 9\nwhile i > 0:\n    i -= 1\n", "HALTS", "A positive counter decreases toward zero."),
    BenchmarkProgram("stride_up", "ranking", "i = 1\nwhile i <= 9:\n    i += 2\n", "HALTS", "The counter increases past a fixed upper bound."),
    BenchmarkProgram("wrong_direction", "recurrent", "i = 5\nwhile i > 0:\n    i += 1\n", "LOOPS", "The update moves away from the guard's exit boundary."),
    BenchmarkProgram("fixed_gap", "modular", "i = 1\nwhile i != 0:\n    i += 2\n", "LOOPS", "Odd values remain odd, so zero is unreachable."),
    BenchmarkProgram("reach_zero", "modular", "i = 10\nwhile i != 0:\n    i -= 2\n", "HALTS", "The target is reached after five updates."),
    BenchmarkProgram("unchanged_counter", "cycle", "i = 4\nwhile i > 0:\n    pass\n", "LOOPS", "The state is unchanged and the guard stays true."),
    BenchmarkProgram("false_on_entry", "guard", "i = 0\nwhile i > 2:\n    i += 1\n", "HALTS", "The loop is skipped because the initial guard is false."),
    BenchmarkProgram("always_true", "constant", "n = 0\nwhile True:\n    n += 1\n", "LOOPS", "A literal true guard has no break in its body."),
    BenchmarkProgram("swap_cycle", "cycle", "a = 1\nb = 2\nwhile a != 0:\n    temp = a\n    a = b\n    b = temp\n", "LOOPS", "Two register values alternate and recreate a complete configuration."),
    BenchmarkProgram("break_counter", "execution", "n = 0\nwhile True:\n    if n >= 5:\n        break\n    n += 1\n", "HALTS", "A branch exits the loop when the counter reaches five."),
    BenchmarkProgram("double_to_limit", "execution", "x = 1\nwhile x < 100:\n    x *= 2\n", "HALTS", "Multiplicative growth crosses the finite bound."),
    BenchmarkProgram("slow_finite", "timeout", "i = 0\nwhile i < 500:\n    i += 1\n", "HALTS", "A long but finite loop is statically proved to terminate."),
    BenchmarkProgram("unbounded_growth", "unknown", "x = 1\nwhile x > 0:\n    x *= 2\n", "UNKNOWN", "The values grow without repeating; available proof rules do not cover it."),
    BenchmarkProgram("zero_sequence", "cycle", "n = 0\nwhile n != 1:\n    if n % 2 == 0:\n        n //= 2\n    else:\n        n = 3 * n + 1\n", "LOOPS", "The value zero is a fixed point of the even branch."),
    BenchmarkProgram("edge_equality", "ranking", "x = 7\nwhile x == 7:\n    x += 1\n", "HALTS", "One update makes the equality condition false."),
]


def run_benchmark(max_steps: int = 300) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in BENCHMARK:
        result = analyze(item.source, max_steps=max_steps)
        # The baseline has only a cutoff: it never detects a repeated state and
        # labels every unfinished run as a loop, which is a guess rather than proof.
        program = compile_source(item.source)
        baseline = execute(program, max_steps=max_steps, detect_cycles=False, keep_trace=False)
        timeout_guess = "HALTS" if baseline.status == "HALTS" else "LOOPS_GUESS"
        rows.append({
            "program": item.name,
            "category": item.category,
            "expected": item.expected,
            "loopscope": result.verdict,
            "method": result.method,
            "steps": result.steps,
            "timeout_baseline": timeout_guess,
            "note": item.note,
        })
    return rows
