"""Rebuild benchmark CSVs, the restricted-template soundness sweep, and report plots."""
from __future__ import annotations

import csv
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from loopscope.analyzer import analyze
from loopscope.benchmark import BENCHMARK, run_benchmark

RESULTS = ROOT / "results"
CHARTS = RESULTS / "charts"
DIAGRAMS = ROOT / "docs" / "diagrams"


def linear_oracle(x: int, op: str, bound: int, delta: int) -> str:
    tests = {
        "<": x < bound, "<=": x <= bound, ">": x > bound,
        ">=": x >= bound, "!=": x != bound,
    }
    if not tests[op]:
        return "HALTS"
    if op == "!=":
        if delta == 0:
            return "LOOPS"
        quotient, remainder = divmod(bound - x, delta)
        return "HALTS" if remainder == 0 and quotient >= 0 else "LOOPS"
    if op in ("<", "<="):
        return "HALTS" if delta > 0 else "LOOPS"
    return "HALTS" if delta < 0 else "LOOPS"


def run_soundness_sweep(count: int = 2400, seed: int = 20261111) -> list[dict[str, object]]:
    rng = random.Random(seed)
    all_cases = [(x, op, b, d) for op in ("<", "<=", ">", ">=", "!=")
                 for x in range(-12, 13) for b in range(-6, 7) for d in range(-3, 4)]
    picked = rng.sample(all_cases, min(count, len(all_cases)))
    rows: list[dict[str, object]] = []
    for index, (x, op, bound, delta) in enumerate(picked, start=1):
        src = f"x = {x}\nwhile x {op} {bound}:\n    x += {delta}\n"
        result = analyze(src)
        expected = linear_oracle(x, op, bound, delta)
        rows.append({
            "case": index, "initial": x, "operator": op, "bound": bound,
            "step": delta, "expected": expected, "loopscope": result.verdict,
            "sound": result.verdict == expected,
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)


def make_pipeline_diagram(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis("off")
    boxes = [
        (0.35, 3.7, 2.1, 1.15, "MiniLoop source\n+ initial values"),
        (3.05, 3.7, 2.1, 1.15, "Parser and\nbytecode compiler"),
        (5.75, 3.7, 2.25, 1.15, "Static proof rules\n(rank / recurrence / !=)"),
        (8.65, 3.7, 2.7, 1.15, "Deterministic execution\n+ configuration memory"),
        (8.65, 1.0, 2.7, 1.15, "HALTS / LOOPS / UNKNOWN\nwith evidence"),
        (5.75, 1.0, 2.25, 1.15, "Optional fixed-width\nfinite-state execution"),
    ]
    for x, y, w, h, label in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor="#EAF1F8", edgecolor="#31506C", linewidth=1.5, joinstyle="round"))
        ax.text(x+w/2, y+h/2, label, ha="center", va="center", fontsize=10)
    arrows = [((2.45,4.27),(3.05,4.27)), ((5.15,4.27),(5.75,4.27)), ((8,4.27),(8.65,4.27)),
              ((10,3.7),(10,2.15)), ((8.65,1.55),(8,1.55)), ((6.85,2.15),(6.85,3.7))]
    for a,b in arrows:
        ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", lw=1.4, color="#34495E"))
    ax.text(8.2, 4.55, "no proof", fontsize=8, color="#34495E")
    ax.text(8.15, 3.05, "runtime", fontsize=8, color="#34495E")
    ax.set_title("LoopScope analysis workflow", fontsize=14, weight="bold", pad=12)
    fig.tight_layout(); fig.savefig(path, dpi=180, bbox_inches="tight"); plt.close(fig)


def make_decidability_diagram(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    ax.add_patch(plt.Rectangle((0.7,0.7),8.6,4.7,fill=False,edgecolor="#34495E",linewidth=1.5))
    ax.add_patch(plt.Circle((4.0,3.2),1.8,fill=True,alpha=.18,color="#4C78A8",ec="#31506C",lw=1.6))
    ax.add_patch(plt.Circle((5.9,3.2),1.8,fill=True,alpha=.18,color="#F2A541",ec="#9C6B21",lw=1.6))
    ax.text(3.35,4.65,"Turing-recognisable",ha="center",fontsize=10,weight="bold")
    ax.text(6.6,4.65,"Co-recognisable",ha="center",fontsize=10,weight="bold")
    ax.text(4.95,3.25,"Decidable\n(intersection)",ha="center",va="center",fontsize=11,weight="bold")
    ax.text(2.45,2.45,"HALT\n(recognisable,\nnot decidable)",ha="center",va="center",fontsize=9)
    ax.text(7.45,2.45,"LOOP = ¬HALT\n(not recognisable)",ha="center",va="center",fontsize=9)
    ax.text(5,0.95,"A language is decidable iff both it and its complement are recognisable.",ha="center",fontsize=9)
    ax.set_title("Recognisability and decidability (conceptual class map)",fontsize=13,weight="bold")
    fig.tight_layout(); fig.savefig(path,dpi=180,bbox_inches="tight"); plt.close(fig)


def make_benchmark_charts(rows: list[dict[str, object]]) -> None:
    verdict_counts = {v: sum(r["loopscope"] == v for r in rows) for v in ("HALTS", "LOOPS", "UNKNOWN")}
    fig, ax = plt.subplots(figsize=(7.4,4.2))
    bars=ax.bar(list(verdict_counts),list(verdict_counts.values()),color=["#4C78A8","#E07B53","#BAB0AC"])
    ax.set_ylabel("Number of programs"); ax.set_title("LoopScope verdicts on the benchmark")
    ax.bar_label(bars); ax.set_ylim(0,max(verdict_counts.values())+2)
    fig.tight_layout(); fig.savefig(CHARTS/"benchmark_verdicts.png",dpi=180); plt.close(fig)

    labels=[r["program"].replace("_","\n") for r in rows]
    category_value = {"LOOPS": 0, "UNKNOWN": 1, "HALTS": 2}
    expected=[category_value[r["expected"]] for r in rows]
    loop=[category_value[r["loopscope"]] for r in rows]
    base=[2 if r["timeout_baseline"]=="HALTS" else 0 for r in rows]
    x=list(range(len(rows))); width=.26
    fig,ax=plt.subplots(figsize=(11,4.8))
    ax.bar([i-width for i in x],expected,width,label="Hand-analysed truth",color="#4C78A8")
    ax.bar(x,loop,width,label="LoopScope",color="#59A14F")
    ax.bar([i+width for i in x],base,width,label="Timeout baseline",color="#E07B53")
    ax.set_xticks(x,labels,fontsize=7); ax.set_yticks([0,1,2], ["LOOPS / timeout guess","UNKNOWN","HALTS"])
    ax.set_ylim(-0.45,2.45)
    ax.set_title("Benchmark outcomes: timeout policy versus proof-oriented analysis")
    ax.legend(ncol=3,fontsize=8,loc="upper center"); ax.grid(axis="y",alpha=.25)
    fig.tight_layout(); fig.savefig(CHARTS/"benchmark_comparison.png",dpi=180); plt.close(fig)


def make_sweep_chart(rows: list[dict[str, object]]) -> None:
    total=len(rows); sound=sum(bool(r["sound"]) for r in rows)
    fig,ax=plt.subplots(figsize=(6.4,4.0))
    bars=ax.bar(["Sound definite\nverdicts","Unsound\nverdicts"],[sound,total-sound],color=["#59A14F","#E07B53"])
    ax.set_ylim(0,total*1.08); ax.set_ylabel("Generated cases")
    ax.set_title(f"Restricted linear-loop sweep (n={total})")
    ax.bar_label(bars,fmt="%d"); fig.tight_layout()
    fig.savefig(CHARTS/"soundness_sweep.png",dpi=180); plt.close(fig)


def make_trace_chart() -> None:
    src="a = 1\nb = 2\nwhile a != 0:\n    t = a\n    a = b\n    b = t\n"
    from loopscope.language import compile_source
    from loopscope.runtime import execute
    result=execute(compile_source(src),max_steps=80)
    trace=result.trace[-24:]
    steps=[r["step"] for r in trace]
    a=[r["env"].get("a",0) for r in trace]
    b=[r["env"].get("b",0) for r in trace]
    fig,ax=plt.subplots(figsize=(7.5,4.0))
    ax.step(steps,a,where="post",label="a",linewidth=1.8)
    ax.step(steps,b,where="post",label="b",linewidth=1.8)
    ax.set_xlabel("Instruction step"); ax.set_ylabel("Register value")
    ax.set_title("Observed register trace before repeated configuration")
    ax.legend(); ax.grid(alpha=.25); fig.tight_layout()
    fig.savefig(CHARTS/"cycle_trace.png",dpi=180); plt.close(fig)


def main() -> None:
    RESULTS.mkdir(exist_ok=True); CHARTS.mkdir(parents=True,exist_ok=True); DIAGRAMS.mkdir(parents=True,exist_ok=True)
    benchmark=run_benchmark(max_steps=300)
    write_csv(RESULTS/"benchmark_results.csv",benchmark)
    sweep=run_soundness_sweep(2400)
    write_csv(RESULTS/"linear_soundness_sweep.csv",sweep)
    make_pipeline_diagram(DIAGRAMS/"analysis_pipeline.png")
    make_decidability_diagram(DIAGRAMS/"decidability_classes.png")
    make_benchmark_charts(benchmark)
    make_sweep_chart(sweep)
    make_trace_chart()
    decided=[r for r in benchmark if r["loopscope"]!="UNKNOWN"]
    correct=sum(r["loopscope"]==r["expected"] for r in decided)
    wrong=len(decided)-correct
    print(f"Benchmark: {len(benchmark)} programs; {len(decided)} definite; {correct} correct; {wrong} incorrect; {len(benchmark)-len(decided)} unknown")
    print(f"Sweep: {len(sweep)} generated single-counter cases; {sum(bool(r['sound']) for r in sweep)} sound; {sum(not bool(r['sound']) for r in sweep)} unsound")
    timeout_wrong=[r["program"] for r in benchmark if r["timeout_baseline"]=="LOOPS_GUESS" and r["expected"]=="HALTS"]
    print("Timeout false positives:", ", ".join(timeout_wrong) if timeout_wrong else "none")

if __name__ == "__main__":
    main()
