"""Command-line interface for LoopScope."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .analyzer import analyze
from .benchmark import BENCHMARK, run_benchmark
from .diagonal import diagonal_demo
from .language import compile_source
from .runtime import execute
from .tm import example_machines, run_tm


def _print_result(name: str, result) -> None:
    print(f"{name:22} {result.verdict:7} via {result.method} ({result.steps} instruction(s))")
    print(f"  {result.explanation}")


def cmd_benchmark(args) -> None:
    rows = run_benchmark(args.max_steps)
    print("LoopScope benchmark (expected outcomes were hand-analysed)")
    print(f"{'program':22} {'expected':9} {'LoopScope':10} {'method':22} {'timeout':14}")
    for r in rows:
        print(f"{r['program']:22} {r['expected']:9} {r['loopscope']:10} {r['method'][:22]:22} {r['timeout_baseline']:14}")
    decided = [r for r in rows if r['loopscope'] != "UNKNOWN"]
    correct = sum(r['loopscope'] == r['expected'] for r in decided)
    wrong = len(decided) - correct
    print(f"\nDecided: {len(decided)}/{len(rows)} | correct definite answers: {correct} | wrong definite answers: {wrong} | UNKNOWN: {len(rows)-len(decided)}")
    if args.csv:
        out = Path(args.csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader(); writer.writerows(rows)
        print(f"Saved {out}")


def cmd_explain(args) -> None:
    choices = {p.name: p for p in BENCHMARK}
    if args.name not in choices:
        raise SystemExit(f"Unknown benchmark name '{args.name}'. Choices: {', '.join(choices)}")
    item = choices[args.name]
    print(f"Program: {item.name}\nSource:\n{item.source}")
    _print_result(item.name, analyze(item.source, max_steps=args.max_steps))


def cmd_analyze(args) -> None:
    path = Path(args.file)
    source = path.read_text(encoding="utf-8")
    result = analyze(source, max_steps=args.max_steps, fixed_bits=args.fixed_bits)
    print(f"File: {path}\nVerdict: {result.verdict}\nMethod: {result.method}\nSteps: {result.steps}\nReason: {result.explanation}")
    if result.execution:
        print(f"Final store: {result.execution.final_env}")
        if result.execution.cycle_length is not None:
            print(f"Repeated configuration: cycle length {result.execution.cycle_length}")


def cmd_diagonal(args) -> None:
    print("Diagonal demonstration (finite meta-level model)")
    for item in diagonal_demo():
        print(f"{item.name:22} predicts {item.predict:5} | diagonal behaviour {item.actual_diagonal_behaviour:5} | wrong={item.is_wrong}")


def cmd_tm(args) -> None:
    for name, (transitions, input_text, start) in example_machines().items():
        result = run_tm(transitions, input_text, start_state=start, max_steps=args.max_steps)
        print(f"{name:22} {result.status:7} after {result.steps:4} step(s): {result.reason}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="loopscope", description="Restricted-case infinite-loop analysis")
    sub = parser.add_subparsers(dest="command", required=True)
    bench = sub.add_parser("benchmark", help="run the bundled benchmark")
    bench.add_argument("--max-steps", type=int, default=300)
    bench.add_argument("--csv")
    bench.set_defaults(func=cmd_benchmark)
    explain = sub.add_parser("explain", help="explain one bundled benchmark program")
    explain.add_argument("name")
    explain.add_argument("--max-steps", type=int, default=300)
    explain.set_defaults(func=cmd_explain)
    user = sub.add_parser("analyze", help="analyse a .loop source file")
    user.add_argument("file")
    user.add_argument("--max-steps", type=int, default=10_000)
    user.add_argument("--fixed-bits", type=int)
    user.set_defaults(func=cmd_analyze)
    diag = sub.add_parser("diagonal", help="show the executable diagonal contradiction")
    diag.set_defaults(func=cmd_diagonal)
    tm = sub.add_parser("tm", help="run the Turing-machine examples")
    tm.add_argument("--max-steps", type=int, default=100)
    tm.set_defaults(func=cmd_tm)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
