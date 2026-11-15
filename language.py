"""Parser, validator, and compiler for the deliberately small LoopScope language."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any


class LanguageError(ValueError):
    """Raised when a source program uses syntax outside the supported language."""


@dataclass(frozen=True)
class Instruction:
    op: str
    arg: Any = None
    target: int | None = None
    line: int = 0


@dataclass
class Program:
    source: str
    tree: ast.Module
    instructions: list[Instruction]


_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Mod)
_ALLOWED_CMPOPS = (ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Eq, ast.NotEq)


def _validate_expr(node: ast.AST) -> None:
    if isinstance(node, ast.Constant):
        if type(node.value) not in (int, bool):
            raise LanguageError(f"Only integer and Boolean constants are allowed (line {getattr(node, 'lineno', '?')}).")
    elif isinstance(node, ast.Name):
        if not node.id.isidentifier():
            raise LanguageError("Invalid variable name.")
    elif isinstance(node, ast.BinOp):
        if not isinstance(node.op, _ALLOWED_BINOPS):
            raise LanguageError(f"Unsupported arithmetic operator at line {node.lineno}.")
        _validate_expr(node.left)
        _validate_expr(node.right)
    elif isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, (ast.UAdd, ast.USub, ast.Not)):
            raise LanguageError(f"Unsupported unary operator at line {node.lineno}.")
        _validate_expr(node.operand)
    elif isinstance(node, ast.Compare):
        if not all(isinstance(op, _ALLOWED_CMPOPS) for op in node.ops):
            raise LanguageError(f"Unsupported comparison at line {node.lineno}.")
        _validate_expr(node.left)
        for item in node.comparators:
            _validate_expr(item)
    elif isinstance(node, ast.BoolOp):
        if not isinstance(node.op, (ast.And, ast.Or)):
            raise LanguageError(f"Unsupported Boolean operator at line {node.lineno}.")
        for value in node.values:
            _validate_expr(value)
    else:
        raise LanguageError(f"Unsupported expression '{type(node).__name__}' at line {getattr(node, 'lineno', '?')}.")


def _binary(op: ast.operator, left: int, right: int) -> int:
    if isinstance(op, ast.Add):
        return left + right
    if isinstance(op, ast.Sub):
        return left - right
    if isinstance(op, ast.Mult):
        return left * right
    if isinstance(op, ast.FloorDiv):
        if right == 0:
            raise ZeroDivisionError("integer division by zero")
        return left // right
    if isinstance(op, ast.Mod):
        if right == 0:
            raise ZeroDivisionError("integer modulo by zero")
        return left % right
    raise LanguageError("Unsupported arithmetic operator.")


def evaluate(node: ast.AST, env: dict[str, int | bool]) -> int | bool:
    """Evaluate a validated expression without Python eval/exec."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in env:
            raise NameError(f"Variable '{node.id}' has not been initialised.")
        return env[node.id]
    if isinstance(node, ast.BinOp):
        left, right = evaluate(node.left, env), evaluate(node.right, env)
        if type(left) is not int or type(right) is not int:
            raise TypeError("Arithmetic operands must be integers.")
        return _binary(node.op, left, right)
    if isinstance(node, ast.UnaryOp):
        value = evaluate(node.operand, env)
        if isinstance(node.op, ast.UAdd):
            return +int(value)
        if isinstance(node.op, ast.USub):
            return -int(value)
        if isinstance(node.op, ast.Not):
            return not bool(value)
    if isinstance(node, ast.Compare):
        left = evaluate(node.left, env)
        for op, right_node in zip(node.ops, node.comparators):
            right = evaluate(right_node, env)
            if isinstance(op, ast.Lt):
                ok = left < right
            elif isinstance(op, ast.LtE):
                ok = left <= right
            elif isinstance(op, ast.Gt):
                ok = left > right
            elif isinstance(op, ast.GtE):
                ok = left >= right
            elif isinstance(op, ast.Eq):
                ok = left == right
            elif isinstance(op, ast.NotEq):
                ok = left != right
            else:  # pragma: no cover - validation prevents this
                raise LanguageError("Unsupported comparison.")
            if not ok:
                return False
            left = right
        return True
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            for value in node.values:
                if not bool(evaluate(value, env)):
                    return False
            return True
        for value in node.values:
            if bool(evaluate(value, env)):
                return True
        return False
    raise LanguageError(f"Unsupported expression '{type(node).__name__}'.")


def _validate_statement(stmt: ast.stmt, loop_depth: int = 0) -> None:
    if isinstance(stmt, ast.Assign):
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            raise LanguageError(f"Only a single variable assignment is supported (line {stmt.lineno}).")
        _validate_expr(stmt.value)
    elif isinstance(stmt, ast.AugAssign):
        if not isinstance(stmt.target, ast.Name) or not isinstance(stmt.op, _ALLOWED_BINOPS):
            raise LanguageError(f"Unsupported augmented assignment (line {stmt.lineno}).")
        _validate_expr(stmt.value)
    elif isinstance(stmt, ast.If):
        _validate_expr(stmt.test)
        for child in stmt.body + stmt.orelse:
            _validate_statement(child, loop_depth)
    elif isinstance(stmt, ast.While):
        if stmt.orelse:
            raise LanguageError(f"while-else is not supported (line {stmt.lineno}).")
        _validate_expr(stmt.test)
        for child in stmt.body:
            _validate_statement(child, loop_depth + 1)
    elif isinstance(stmt, ast.Break):
        if loop_depth == 0:
            raise LanguageError(f"break must appear inside a while loop (line {stmt.lineno}).")
    elif isinstance(stmt, ast.Pass):
        return
    else:
        raise LanguageError(f"Unsupported statement '{type(stmt).__name__}' at line {getattr(stmt, 'lineno', '?')}.")


def compile_source(source: str) -> Program:
    """Compile a MiniLoop source string to a small deterministic instruction list."""
    if not source.strip():
        raise LanguageError("Program is empty.")
    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError as exc:
        raise LanguageError(f"Syntax error on line {exc.lineno}: {exc.msg}") from exc
    for stmt in tree.body:
        _validate_statement(stmt)

    code: list[Instruction] = []
    break_stacks: list[list[int]] = []

    def emit(op: str, arg: Any = None, target: int | None = None, line: int = 0) -> int:
        code.append(Instruction(op=op, arg=arg, target=target, line=line))
        return len(code) - 1

    def patch(index: int, target: int) -> None:
        old = code[index]
        code[index] = Instruction(old.op, old.arg, target, old.line)

    def compile_block(statements: list[ast.stmt]) -> None:
        for stmt in statements:
            line = getattr(stmt, "lineno", 0)
            if isinstance(stmt, ast.Assign):
                emit("SET", (stmt.targets[0].id, stmt.value), line=line)
            elif isinstance(stmt, ast.AugAssign):
                emit("UPDATE", (stmt.target.id, stmt.op, stmt.value), line=line)
            elif isinstance(stmt, ast.Pass):
                emit("NOP", line=line)
            elif isinstance(stmt, ast.If):
                branch = emit("JIF", stmt.test, line=line)
                compile_block(stmt.body)
                if stmt.orelse:
                    skip_else = emit("JMP", line=line)
                    patch(branch, len(code))
                    compile_block(stmt.orelse)
                    patch(skip_else, len(code))
                else:
                    patch(branch, len(code))
            elif isinstance(stmt, ast.While):
                loop_start = len(code)
                exit_jump = emit("JIF", stmt.test, line=line)
                break_stacks.append([])
                compile_block(stmt.body)
                emit("JMP", target=loop_start, line=line)
                loop_end = len(code)
                patch(exit_jump, loop_end)
                for break_jump in break_stacks.pop():
                    patch(break_jump, loop_end)
            elif isinstance(stmt, ast.Break):
                if not break_stacks:
                    raise LanguageError("break must be inside a loop.")
                jump = emit("JMP", line=line)
                break_stacks[-1].append(jump)
            else:  # pragma: no cover - validator prevents this
                raise LanguageError(f"Unsupported statement {type(stmt).__name__}.")

    compile_block(tree.body)
    emit("HALT", line=0)
    return Program(source=source, tree=tree, instructions=code)
