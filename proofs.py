"""Small, explicit static proof rules for single-counter loops."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any

from .language import evaluate, LanguageError


@dataclass(frozen=True)
class StaticProof:
    verdict: str
    rule: str
    explanation: str
    variable: str | None = None
    initial_value: int | None = None
    bound: int | None = None
    step: int | None = None


def _comparison_value(op: ast.cmpop, left: int, right: int) -> bool:
    if isinstance(op, ast.Lt): return left < right
    if isinstance(op, ast.LtE): return left <= right
    if isinstance(op, ast.Gt): return left > right
    if isinstance(op, ast.GtE): return left >= right
    if isinstance(op, ast.Eq): return left == right
    if isinstance(op, ast.NotEq): return left != right
    raise LanguageError("Unsupported comparison in proof rule.")


def prove_simple_loop(source: str) -> StaticProof | None:
    """Prove selected single-loop programs; return None outside this small fragment."""
    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError:
        return None
    loops = [s for s in tree.body if isinstance(s, ast.While)]
    if len(loops) != 1:
        return None
    loop = loops[0]
    loop_index = tree.body.index(loop)
    if loop.orelse or loop_index != len(tree.body) - 1:
        return None

    env: dict[str, int | bool] = {}
    try:
        for stmt in tree.body[:loop_index]:
            if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                return None
            env[stmt.targets[0].id] = evaluate(stmt.value, env)
    except Exception:
        return None

    if not isinstance(loop.test, ast.Compare) or len(loop.test.ops) != 1 or len(loop.test.comparators) != 1:
        if isinstance(loop.test, ast.Constant) and type(loop.test.value) is bool:
            if loop.test.value and not any(isinstance(x, ast.Break) for x in ast.walk(loop)):
                return StaticProof("LOOPS", "constant-true", "The guard is always true and the loop body contains no break statement.")
            if not loop.test.value:
                return StaticProof("HALTS", "constant-false", "The loop guard is false before the first iteration.")
        return None

    if not isinstance(loop.test.left, ast.Name):
        return None
    variable = loop.test.left.id
    if variable not in env or not isinstance(loop.test.ops[0], (ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Eq, ast.NotEq)):
        return None
    try:
        bound_value = evaluate(loop.test.comparators[0], env)
    except Exception:
        return None
    if type(env[variable]) is not int or type(bound_value) is not int:
        return None
    initial = int(env[variable])
    bound = int(bound_value)
    op = loop.test.ops[0]

    # The proof fragment requires one update (or pass) to the guarded variable.
    body = [s for s in loop.body if not isinstance(s, ast.Pass)]
    if len(body) > 1:
        return None
    delta = 0
    if body:
        update = body[0]
        if not isinstance(update, ast.AugAssign) or not isinstance(update.target, ast.Name) or update.target.id != variable:
            return None
        if not isinstance(update.op, (ast.Add, ast.Sub)):
            return None
        try:
            amount = evaluate(update.value, env)
        except Exception:
            return None
        if type(amount) is not int:
            return None
        delta = amount if isinstance(update.op, ast.Add) else -amount

    initially_true = _comparison_value(op, initial, bound)
    if not initially_true:
        return StaticProof("HALTS", "false-on-entry", f"The guard is false initially ({variable}={initial}, bound={bound}); no iteration is entered.", variable, initial, bound, delta)

    if isinstance(op, ast.NotEq):
        if delta == 0:
            return StaticProof("LOOPS", "unchanged-counter", f"{variable} remains {initial}; the != guard stays true forever.", variable, initial, bound, delta)
        distance = bound - initial
        quotient, remainder = divmod(distance, delta)
        if remainder == 0 and quotient >= 0:
            return StaticProof("HALTS", "reachable-target", f"The target {bound} is reached after exactly {quotient} update(s), since ({bound} - {initial}) / {delta} is a non-negative integer.", variable, initial, bound, delta)
        return StaticProof("LOOPS", "unreachable-target", f"The sequence {initial} + n*({delta}) never equals {bound} for an integer n >= 0 (wrong direction or non-divisible difference).", variable, initial, bound, delta)

    if isinstance(op, ast.Eq):
        if delta == 0:
            return StaticProof("LOOPS", "stable-equality", f"The equality guard remains true because {variable} never changes.", variable, initial, bound, delta)
        return StaticProof("HALTS", "equality-exit", f"The first update changes {variable} from {initial}, so the equality guard becomes false.", variable, initial, bound, delta)

    if isinstance(op, (ast.Lt, ast.LtE)):
        if delta > 0:
            rank = f"{bound} - {variable}" if isinstance(op, ast.Lt) else f"{bound} - {variable} + 1"
            return StaticProof("HALTS", "ascending-ranking", f"The ranking function R = {rank} is a positive integer while the guard is true and decreases by {delta} on each iteration; therefore the guard must eventually become false.", variable, initial, bound, delta)
        return StaticProof("LOOPS", "ascending-recurrence", f"The counter moves by {delta} per iteration, away from the upper exit boundary; the guard remains true.", variable, initial, bound, delta)

    if isinstance(op, (ast.Gt, ast.GtE)):
        if delta < 0:
            rank = f"{variable} - {bound}" if isinstance(op, ast.Gt) else f"{variable} - {bound} + 1"
            return StaticProof("HALTS", "descending-ranking", f"The ranking function R = {rank} is a positive integer while the guard is true and decreases by {abs(delta)} on each iteration; termination follows.", variable, initial, bound, delta)
        return StaticProof("LOOPS", "descending-recurrence", f"The counter moves by {delta} per iteration, away from the lower exit boundary; the guard remains true.", variable, initial, bound, delta)

    return None
