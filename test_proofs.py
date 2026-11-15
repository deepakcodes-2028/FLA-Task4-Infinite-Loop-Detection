from loopscope.analyzer import analyze
from loopscope.proofs import prove_simple_loop


def test_ranking_function_proves_termination():
    result = analyze("i = 8\nwhile i > 0:\n    i -= 2\n")
    assert result.verdict == "HALTS"
    assert result.method == "static-proof"
    assert "ranking function" in result.explanation


def test_recurrent_condition_proves_nontermination():
    result = analyze("i = 10\nwhile i > 0:\n    i += 1\n")
    assert result.verdict == "LOOPS"
    assert result.method == "static-proof"


def test_unreachable_inequality_target_proves_loop():
    result = analyze("i = 1\nwhile i != 0:\n    i += 2\n")
    assert result.verdict == "LOOPS"
    assert "never equals" in result.explanation


def test_reachable_inequality_target_proves_halt():
    result = analyze("i = 9\nwhile i != 1:\n    i -= 2\n")
    assert result.verdict == "HALTS"


def test_false_guard_on_entry_proves_halt():
    result = analyze("i = 0\nwhile i > 4:\n    i += 1\n")
    assert result.verdict == "HALTS"
    assert result.static_proof.rule == "false-on-entry"


def test_literal_true_without_break_proves_loop():
    result = analyze("i = 0\nwhile True:\n    i += 1\n")
    assert result.verdict == "LOOPS"
    assert result.static_proof.rule == "constant-true"


def test_equality_guard_breaks_after_one_update():
    result = analyze("i = 5\nwhile i == 5:\n    i += 1\n")
    assert result.verdict == "HALTS"


def test_complex_loop_is_not_claimed_static():
    proof = prove_simple_loop("x = 1\nwhile x < 20:\n    x *= 2\n")
    assert proof is None
    assert analyze("x = 1\nwhile x < 20:\n    x *= 2\n").verdict == "HALTS"
