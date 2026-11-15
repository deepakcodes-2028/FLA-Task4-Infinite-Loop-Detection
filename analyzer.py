"""Public analysis pipeline: static proof first, deterministic execution second."""
from __future__ import annotations

from dataclasses import dataclass
from .language import compile_source, LanguageError
from .proofs import prove_simple_loop, StaticProof
from .runtime import execute, ExecutionResult


@dataclass
class AnalysisResult:
    verdict: str
    method: str
    explanation: str
    steps: int = 0
    static_proof: StaticProof | None = None
    execution: ExecutionResult | None = None


def analyze(source: str, *, max_steps: int = 10_000, fixed_bits: int | None = None) -> AnalysisResult:
    """Return HALTS, LOOPS, or UNKNOWN. Fixed-width mode uses wraparound semantics."""
    try:
        program = compile_source(source)
    except LanguageError as exc:
        return AnalysisResult("UNKNOWN", "parser", str(exc))

    if fixed_bits is None:
        proof = prove_simple_loop(source)
        if proof is not None:
            return AnalysisResult(proof.verdict, "static-proof", proof.explanation, 0, static_proof=proof)

    result = execute(program, max_steps=max_steps, fixed_bits=fixed_bits)
    method = "configuration-cycle" if result.status == "LOOPS" else "bounded-execution"
    if result.status == "HALTS":
        method = "execution"
    if fixed_bits is not None:
        method += f" ({fixed_bits}-bit unsigned registers)"
    return AnalysisResult(result.status, method, result.reason, result.steps, execution=result)
