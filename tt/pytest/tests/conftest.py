from Pyjo.File import curfile

import pytest


@pytest.fixture
def app():
    return curfile().dirname().sibling('myapp.py')
