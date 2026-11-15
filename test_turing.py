from loopscope.tm import example_machines, run_tm


def test_tm_halts_when_designated_state_is_reached():
    transitions, data, start = example_machines()["erase_and_halt"]
    assert run_tm(transitions, data, start_state=start).status == "HALTS"


def test_tm_repeated_configuration_is_a_loop_proof():
    transitions, data, start = example_machines()["two_cell_oscillator"]
    result = run_tm(transitions, data, start_state=start)
    assert result.status == "LOOPS"
    assert result.cycle_length == 2


def test_tm_growing_tape_is_unknown_at_budget():
    transitions, data, start = example_machines()["right_writer"]
    assert run_tm(transitions, data, start_state=start, max_steps=40).status == "UNKNOWN"
