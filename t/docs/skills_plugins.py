import Pyjo.File

from Pyjo.Test import *

import importlib
import os
import re
import subprocess
import sys


# The distribution of plugins/pyjoyment/skills/plugins/SKILL.md, each block of code in the file that its first line
# names, as a coding agent writes it, whose test runs as the skill runs it, with the module of the checkout
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Skills = importlib.import_module('Skills')

root = Pyjo.File.curfile().dirname().dirname().dirname()
env = dict(os.environ)
env['PYTHONPATH'] = os.pathsep.join([root.to_str(), *filter(None, [env.get('PYTHONPATH')])])
for name in ('PYJO_HARNESS_ACTIVE', 'PYJO_HARNESS_IS_VERBOSE', 'PYJO_LOG_LEVEL'):
    env.pop(name, None)

tmp = Pyjo.File.tempdir()
names = []
for language in ('python', 'toml'):
    for code in Skills.blocks('plugins', language):
        names.append(re.match(r'# (\S+)\n', code)[1])
        tmp.child(*names[-1].split('/')).dirname().make_path()
        tmp.child(*names[-1].split('/')).spew(code)
is_deeply_ok(sorted(names), ['Pyjoyment/Plugin/Greeting.py', 'pyproject.toml', 't/basic.py'], 'files of the project')
ok(not os.path.exists(tmp.child('Pyjoyment', '__init__.py').to_str()), 'a namespace package')

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
