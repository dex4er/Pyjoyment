import Pyjo.File

from Pyjo.Test import *

import os
import subprocess
import sys


# The example itself, in a process of its own, as the workflow Build runs it with the wheel: its server listens on a port
# that the system picks, so it needs no free port of the tests
ROOT = Pyjo.File.curfile().dirname().dirname().dirname().to_str()
script = Pyjo.File.path(ROOT, 'examples', 'loopback.py').to_str()
result = subprocess.run(
    [sys.executable, script], env={**os.environ, 'PYTHONPATH': ROOT}, capture_output=True, text=True, timeout=60
)
is_ok(result.stdout, '200 Your Pyjo is working!\n', 'the response of the server')
is_ok(result.stderr, '', 'nothing on the standard error')
is_ok(result.returncode, 0, 'the server and the user agent closed at the end')

done_testing()
