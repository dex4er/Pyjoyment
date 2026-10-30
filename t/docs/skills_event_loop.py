import Pyjo.File

from Pyjo.Test import *

import importlib
import os
import re
import subprocess
import sys


# The scripts of plugins/pyjoyment/skills/event-loop/SKILL.md, each in the file that its first line names, as a coding
# agent writes them, run as they are
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Skills = importlib.import_module('Skills')

root = Pyjo.File.curfile().dirname().dirname().dirname()
env = dict(os.environ)
env['PYTHONPATH'] = os.pathsep.join([root.to_str(), *filter(None, [env.get('PYTHONPATH')])])

tmp = Pyjo.File.tempdir()
names = []
for code in Skills.blocks('event-loop'):
    names.append(re.match(r'# (\S+)\n', code)[1])
    tmp.child(names[-1]).spew(code)
is_deeply_ok(names, ['echo.py', 'coroutines.py', 'processes.py', 'daemon.py'], 'four scripts')


def run(name):
    p = subprocess.run([sys.executable, name], cwd=tmp.to_str(), env=env, capture_output=True, text=True, timeout=60)
    return p.stdout, p.stderr, p.returncode


with subtest('A server and a client of TCP'):
    stdout, stderr, status = run('echo.py')
    is_ok(status, 0, 'success')
    is_ok(stdout, 'echo: hello\n', 'answer')
    unlike_ok(stderr, r'ResourceWarning', 'nothing left open')

with subtest('Promises and coroutines'):
    stdout, stderr, status = run('coroutines.py')
    is_ok(status, 0, 'success')
    is_ok(stdout, 'HELLO\n', 'answer')
    unlike_ok(stderr, r'ResourceWarning', 'nothing left open')

with subtest('Processes and UDP'):
    if sys.platform == 'win32':
        skip('Windows has no pipes that the event loop watches', 3)
    else:
        stdout, stderr, status = run('processes.py')
        is_ok(status, 0, 'success')
        is_ok(stdout, '0 from the child\npong ping\n', 'child and datagram')
        unlike_ok(stderr, r'ResourceWarning', 'nothing left open')

with subtest('An HTTP server without the framework'):
    stdout, stderr, status = run('daemon.py')
    is_ok(status, 0, 'success')
    is_ok(stdout, 'Hello /world!\n', 'response')
    unlike_ok(stderr, r'ResourceWarning', 'nothing left open')

done_testing()
