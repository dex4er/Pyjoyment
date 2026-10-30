import Pyjo.File
import Pyjo.Test.Pyjo

from Pyjo.Test import *

import importlib
import os
import re
import subprocess
import sys


# The application of plugins/pyjoyment/skills/deploy/SKILL.md in the file that its first line names, as a coding agent
# writes it, with its probes, and the generators and the options of the servers that the skill names
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
Skills = importlib.import_module('Skills')

root = Pyjo.File.curfile().dirname().dirname().dirname()
env = dict(os.environ)
env['PYTHONPATH'] = os.pathsep.join([root.to_str(), *filter(None, [env.get('PYTHONPATH')])])
env['PYJO_LOG_LEVEL'] = 'fatal'

tmp = Pyjo.File.tempdir()
(code,) = Skills.blocks('deploy')
app = tmp.child(re.match(r'# (\S+)\n', code)[1]).spew(code)
is_ok(app.basename(), 'app.py', 'application')


def run(*args):
    p = subprocess.run([sys.executable, *args], cwd=tmp.to_str(), env=env, capture_output=True, text=True, timeout=60)
    return p.stdout, p.returncode


with subtest('Probes'):
    t = Pyjo.Test.Pyjo.new(app)
    t.app.log.level = 'fatal'
    t.get_ok('/').status_is(200).content_is('Hello from development')
    t.get_ok('/livez').status_is(200).content_is('ok')
    t.get_ok('/healthz').status_is(200)
    t.get_ok('/readyz').status_is(200).content_is('ok')

with subtest('Generators'):
    for generator in (['pyproject'], ['dockerfile', '-p', '8080'], ['kubernetes', '-i', 'myapp']):
        stdout, status = run('app.py', 'generate', *generator)
        is_ok(status, 0, f'generate {generator[0]}')
    ok(os.path.isfile(tmp.child('pyproject.toml').to_str()), 'pyproject.toml')
    dockerfile = tmp.child('Dockerfile').slurp().decode()
    like_ok(dockerfile, r'CMD \["python", "app.py", "prefork"\]', 'prefork')
    like_ok(dockerfile, r'HEALTHCHECK .*/livez', 'HEALTHCHECK of /livez')
    for name in ('base/kustomization.yaml', 'dev/kustomization.yaml', 'prod/kustomization.yaml'):
        ok(os.path.isfile(tmp.child('kubernetes', *name.split('/')).to_str()), f'kubernetes/{name}')
    like_ok(tmp.child('kubernetes', 'base', 'probes.yaml').slurp().decode(), r'/readyz', 'readiness probe')

with subtest('Options of the servers'):
    stdout, status = run('app.py', 'prefork', '--help')
    for option in ('-w, --workers', '-l, --listen', '-p, --proxy', '-G, --graceful-timeout', '-S, --shutdown-delay'):
        like_ok(stdout, re.escape(option), option)
    stdout, status = run('app.py', 'generate', 'dockerfile', '--help')
    for option in ('-p, --port', '-G, --graceful-timeout', '-t, --target', '-u, --user'):
        like_ok(stdout, re.escape(option), option)

done_testing()
