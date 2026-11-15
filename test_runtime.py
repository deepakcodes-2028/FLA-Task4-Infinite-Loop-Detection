from loopscope.analyzer import analyze


def test_repeated_configuration_proves_cycle():
    source = "a = 1\nb = 2\nwhile a != 0:\n    t = a\n    a = b\n    b = t\n"
    result = analyze(source, max_steps=200)
    assert result.verdict == "LOOPS"
    assert result.execution.cycle_length is not None


def test_break_program_halts():
    source = "n = 0\nwhile True:\n    if n >= 4:\n        break\n    n += 1\n"
    assert analyze(source).verdict == "HALTS"


def test_growth_without_repeat_returns_unknown():
    source = "x = 1\nwhile x > 0:\n    x *= 2\n"
    result = analyze(source, max_steps=300)
    assert result.verdict == "UNKNOWN"


def test_fixed_width_wraparound_changes_behaviour():
    source = "i = 10\nwhile i > 0:\n    i += 1\n"
    unbounded = analyze(source)
    bounded = analyze(source, fixed_bits=8, max_steps=2_000)
    assert unbounded.verdict == "LOOPS"
    assert bounded.verdict == "HALTS"
    assert bounded.execution.final_env["i"] == 0


def test_timeout_is_not_a_proof():
    source = "i = 0\nwhile i < 1000:\n    i += 1\n"
    result = analyze(source, max_steps=10)
    # The static proof is independent of the execution cutoff.
    assert result.verdict == "HALTS"
