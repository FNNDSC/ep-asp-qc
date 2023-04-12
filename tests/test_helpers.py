import pytest
from pathlib import Path

from surfigures.inputs.find import _fname_without_side


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ('hello-left', 'hello'),
        ('hello-LEFT', 'hello'),
        ('hello-right', 'hello'),
        ('hello-left-suffix', 'hello-suffix'),
        ('hello-LEFT-suffix', 'hello-suffix'),
        ('left-hello', 'hello'),
        ('right-hello', 'hello')
    ]
)
def test_replace_side(input_str, expected):
    assert _fname_without_side(Path(input_str)) == expected
