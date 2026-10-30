import Pyjo.File

from Pyjo.Test import *

import importlib
import os
import re
import subprocess
import sys


# The project of plugins/pyjoyment/skills/app/SKILL.md, each block of code in the file that its first line names, as a
# coding agent writes it, whose tests and commands run as the skill runs them
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Skills = importlib.import_module('Skills')

root = Pyjo.File.curfile().dirname().dirname().dirname()
env = dict(os.environ)
env['PYTHONPATH'] = os.pathsep.join([root.to_str(), *filter(None, [env.get('PYTHONPATH')])])
for name in ('PYJO_HARNESS_ACTIVE', 'PYJO_HARNESS_IS_VERBOSE', 'PYJO_LOG_LEVEL'):
    env.pop(name, None)

tmp = Pyjo.File.tempdir()
names = []
for language in ('python', 'html', 'yaml'):
    for code in Skills.blocks('app', language):
        names.append(re.match(r'%?# (\S+)\n', code)[1])
        tmp.child(*names[-1].split('/')).dirname().make_path()
        tmp.child(*names[-1].split('/')).spew(code)
is_deeply_ok(
    sorted(names),
    [
        'MyApp/Controller/Auth.py',
        'MyApp/Controller/Notes.py',
        'MyApp/Model/Notes.py',
        'MyApp/__init__.py',
        'MyApp/__main__.py',
        'my_app.yml',
        't/notes.py',
        'templates/layouts/default.html.ep',
        'templates/notes/index.html.ep',
        'templates/notes/show.html.ep',
    ],
    'files of the project',
)


def run(*args):
    p = subprocess.run([sys.executable, *args], cwd=tmp.to_str(), env=env, capture_output=True, text=True, timeout=120)
    return p.stdout, p.stderr, p.returncode


with subtest('Tests of the project'):
    stdout, stderr, status = run('-m', 'Pyjo.Prove', '-l', '-v', '-r', 't')
    is_ok(status, 0, 'passed')
    like_ok(stdout, r'All tests successful\.', 'all')

with subtest('Routes'):
    stdout, stderr, status = run('-m', 'MyApp', 'routes')
    is_ok(status, 0, 'success')
    like_ok(stdout, r'/notes/<id:num>\s+GET\s+"note"', 'named route')
    like_ok(stdout, re.compile(r'^/api\s+\*.*\n\s+\+/notes\s+POST', re.M), 'nested route')

done_testing()
