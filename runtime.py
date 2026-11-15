"""Deterministic register-machine execution with optional configuration-cycle detection."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .language import Program, evaluate, _binary


@dataclass
class ExecutionResult:
    status: str
    steps: int
    final_env: dict[str, int | bool]
    reason: str
    cycle_start: int | None = None
    cycle_length: int | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)


def _wrap(value: int | bool, fixed_bits: int | None) -> int | bool:
    if fixed_bits is None or type(value) is not int:
        return value
    if fixed_bits < 1 or fixed_bits > 32:
        raise ValueError("fixed_bits must be between 1 and 32.")
    return value % (1 << fixed_bits)


def execute(
    program: Program,
    *,
    inputs: dict[str, int | bool] | None = None,
    max_steps: int = 10_000,
    fixed_bits: int | None = None,
    detect_cycles: bool = True,
    keep_trace: bool = True,
) -> ExecutionResult:
    """Run compiled code. A repeated (PC, store) proves a deterministic cycle."""
    if max_steps < 1:
        raise ValueError("max_steps must be positive.")
    env: dict[str, int | bool] = dict(inputs or {})
    if fixed_bits is not None and not (1 <= fixed_bits <= 32):
        raise ValueError("fixed_bits must be between 1 and 32.")
    env = {k: _wrap(v, fixed_bits) for k, v in env.items()}
    pc = 0
    steps = 0
    seen: dict[tuple[Any, ...], int] = {}
    trace: list[dict[str, Any]] = []
    code = program.instructions

    while steps < max_steps:
        if pc < 0 or pc >= len(code):
            return ExecutionResult("HALTS", steps, dict(env), "Program counter left the instruction sequence.", trace=trace)
        key = (pc, tuple(sorted(env.items())))
        if detect_cycles and key in seen:
            start = seen[key]
            return ExecutionResult(
                "LOOPS", steps, dict(env), "A complete machine configuration repeated; determinism forces the same cycle again.",
                cycle_start=start, cycle_length=steps - start, trace=trace
            )
        if detect_cycles:
            seen[key] = steps
        instruction = code[pc]
        if keep_trace and len(trace) < 5_000:
            trace.append({"step": steps, "pc": pc, "op": instruction.op, "env": dict(env)})
        steps += 1
        try:
            if instruction.op == "SET":
                name, expr = instruction.arg
                env[name] = _wrap(evaluate(expr, env), fixed_bits)
                pc += 1
            elif instruction.op == "UPDATE":
                name, op, expr = instruction.arg
                if name not in env:
                    raise NameError(f"Variable '{name}' has not been initialised.")
                old = env[name]
                rhs = evaluate(expr, env)
                if type(old) is not int or type(rhs) is not int:
                    raise TypeError("Augmented arithmetic requires integer operands.")
                env[name] = _wrap(_binary(op, old, rhs), fixed_bits)
                pc += 1
            elif instruction.op == "JIF":
                condition = bool(evaluate(instruction.arg, env))
                pc = pc + 1 if condition else int(instruction.target)
            elif instruction.op == "JMP":
                pc = int(instruction.target)
            elif instruction.op == "NOP":
                pc += 1
            elif instruction.op == "HALT":
                return ExecutionResult("HALTS", steps, dict(env), "The HALT instruction was reached.", trace=trace)
            else:  # pragma: no cover
                raise RuntimeError(f"Unknown instruction: {instruction.op}")
        except Exception as exc:
            return ExecutionResult("UNKNOWN", steps, dict(env), f"Execution could not continue safely: {type(exc).__name__}: {exc}", trace=trace)

    return ExecutionResult("UNKNOWN", steps, dict(env), f"Execution budget of {max_steps} instructions was exhausted.", trace=trace)
