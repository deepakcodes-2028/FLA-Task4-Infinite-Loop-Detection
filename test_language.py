import pytest
from loopscope.language import compile_source, LanguageError
from loopscope.runtime import execute


def test_compile_simple_countdown():
    p = compile_source("i = 3\nwhile i > 0:\n    i -= 1\n")
    result = execute(p)
    assert result.status == "HALTS"
    assert result.final_env["i"] == 0


def test_if_and_break_are_compiled():
    p = compile_source("i = 0\nwhile True:\n    if i == 3:\n        break\n    i += 1\n")
    assert execute(p).status == "HALTS"


def test_function_calls_are_rejected():
    with pytest.raises(LanguageError):
        compile_source("while True:\n    print('unsafe')\n")


def test_uninitialised_variable_is_not_guessed():
    p = compile_source("while x > 0:\n    x -= 1\n")
    assert execute(p).status == "UNKNOWN"
