import pytest
from pathlib import Path

from surfigures.inputs import fname_without_side, name_tempfile_if_endswith


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
    assert fname_without_side(Path(input_str)) == expected


@pytest.mark.parametrize(
    'p, expected',
    [
        (Path('surf_81920.disterr.txt'), Path('/tmp/surf_81920.abs.disterr.txt')),
        (Path('surf_81920.smtherr.txt'), None),
    ]
)
def test_insert_before_suffix_if(p, expected):
    actual = name_tempfile_if_endswith(p, '.disterr.txt', '.abs', Path('/tmp'))
    assert actual == expected
