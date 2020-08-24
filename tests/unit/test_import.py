#!/usr/bin/python
# Test utilities methods without GUI
import pytest
import sys

def test_1():
    """
    test main
    :return:
    """
    print(f'test 1: {sys.path}')
    import pyrs
    print(pyrs)
    assert 1 == 2


def test_2():
    if '' in sys.path:
        sys.path.remove('')
    else:
        assert 1 == 3
    import pyrs
    print(pyrs)
    assert 11 == 22


if __name__ == '__main__':
    pytest.main()
