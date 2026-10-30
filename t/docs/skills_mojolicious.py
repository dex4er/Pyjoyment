import Pyjo.File

from Pyjo.Test import *

import importlib
import os
import re
import subprocess
import sys


# The Python of plugins/pyjoyment/skills/mojolicious/SKILL.md, each block of code in the file that its first line
# names, as a coding agent ports the Perl next to it, whose test runs as the skill runs it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Skills = importlib.import_module('Skills')

root = Pyjo.File.curfile().dirname().dirname().dirname()
env = dict(os.environ)
env['PYTHONPATH'] = os.pathsep.join([root.to_str(), *filter(None, [env.get('PYTHONPATH')])])
for name in ('PYJO_HARNESS_ACTIVE', 'PYJO_HARNESS_IS_VERBOSE', 'PYJO_LOG_LEVEL'):
    env.pop(name, None)

tmp = Pyjo.File.tempdir()
names = []
for code in Skills.blocks('mojolicious'):
    names.append(re.match(r'# (\S+)\n', code)[1])
    tmp.child(*names[-1].split('/')).dirname().make_path()
    tmp.child(*names[-1].split('/')).spew(code)
is_deeply_ok(sorted(names), ['app.py', 't/app.py'], 'the application and its test')
is_ok(len(Skills.blocks('mojolicious', 'perl')), 2, 'next to the Perl of each')

p = subprocess.run(
    [sys.executable, '-m', 'Pyjo.Prove', '-l', '-v', '-r', 't'],
    cwd=tmp.to_str(),
    env=env,
    capture_output=True,
    text=True,
    timeout=120,
)
is_ok(p.returncode, 0, 'the test passes')
like_ok(p.stdout, r'All tests successful\.', 'all')

done_testing()
