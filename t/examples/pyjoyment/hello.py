import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *


# The application of examples/hello.py, which the test loads without starting a server
t = Pyjo.Test.Pyjo.new(curfile().dirname().dirname().dirname().sibling('examples', 'pyjoyment', 'hello.py'))

with subtest('Text'):
    t.get_ok('/').status_is(200).content_type_is('text/html;charset=UTF-8').content_is('I ♥ Pyjoyment!')

done_testing()
