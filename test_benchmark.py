from loopscope.benchmark import BENCHMARK, run_benchmark


def test_benchmark_has_no_wrong_definite_answers():
    rows = run_benchmark(max_steps=300)
    assert len(rows) == len(BENCHMARK)
    definite = [row for row in rows if row["loopscope"] != "UNKNOWN"]
    assert all(row["loopscope"] == row["expected"] for row in definite)
    assert any(row["loopscope"] == "UNKNOWN" for row in rows)


def test_slow_finite_program_is_not_mislabelled_by_loopscope():
    rows = {row["program"]: row for row in run_benchmark(max_steps=300)}
    row = rows["slow_finite"]
    assert row["expected"] == "HALTS"
    assert row["loopscope"] == "HALTS"
    assert row["timeout_baseline"] == "LOOPS_GUESS"
