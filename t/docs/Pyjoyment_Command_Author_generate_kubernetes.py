import Pyjo.File
import Pyjo.Home
import Pyjoyment
import Pyjoyment.Command.Author.generate.kubernetes

from Pyjo.Test import *

import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys


cwd = Pyjo.File.path()
exe = os.environ.pop('PYJO_EXE', None)
python = f'{sys.version_info.major}.{sys.version_info.minor}'
kubectl = shutil.which('kubectl')


def generate(dir, *args):
    os.chdir(dir)
    try:
        with contextlib.redirect_stdout(io.StringIO()) as output:
            kubernetes.run(*args)
    finally:
        os.chdir(cwd)
    return output.getvalue()


def read(dir, name):
    return dir.child('kubernetes', *name.split('/')).slurp().decode()


def project():
    tmp = Pyjo.File.tempdir()
    tmp.child('pyproject.toml').spew('[project]\nname = "my_app"\n')
    return tmp


def script(tmp, content=''):
    tmp.child('myapp.py').spew(content)
    application.home = Pyjo.Home.new(tmp.to_str())
    os.environ['PYJO_EXE'] = tmp.child('myapp.py').to_str()


with subtest('Synopsis'):
    application = Pyjoyment.new()
    kubernetes = Pyjoyment.Command.Author.generate.kubernetes.new(app=application)
    like_ok(
        kubernetes.usage,
        r'^Usage: APPLICATION generate kubernetes \[OPTIONS\] \[-- SERVER OPTIONS\]\n\n  \./myapp\.py generate kubernetes\n',
        'usage',
    )
    like_ok(kubernetes.usage, r'-i, --image <name>', 'option of the image')
    like_ok(kubernetes.usage, r'    --host-path', 'option of the host path')
    like_ok(kubernetes.usage, r'-p, --port <port>', 'option of the port')
    like_ok(kubernetes.usage, r'-G, --graceful-timeout <seconds>', 'option of the graceful timeout')
    like_ok(kubernetes.usage, r'    --dev ', 'option of the group dev')
    like_ok(kubernetes.usage, r'-s, --server <name>', 'option of the server')

    # python -m MyApp generate kubernetes
    tmp = project()
    generate(tmp)
    like_ok(read(tmp, 'base/deployment.yaml'), r'(?m)^  name: pyjoyment$', 'name of the application')
    like_ok(read(tmp, 'dev/deployment.yaml'), r'exec /uv/venv/bin/python -m Pyjoyment daemon"', 'daemon of the package')
    unlike_ok(read(tmp, 'prod/kustomization.yaml'), r'images:', 'image of the name of the application')

    # python -m MyApp generate kubernetes --image ghcr.io/me/myapp:1.0
    tmp = project()
    generate(tmp, '--image', 'ghcr.io/me/myapp:1.0')
    like_ok(
        read(tmp, 'prod/kustomization.yaml'),
        r'(?m)^images:\n  - name: pyjoyment\n    newName: ghcr\.io/me/myapp:1\.0$',
        'image of prod',
    )

    # python -m MyApp generate kubernetes --host-path
    tmp = project()
    generate(tmp, '--host-path')
    # The directory of the project, as the system gives it, with the short names of 8.3 on Windows
    path = re.search(r'hostPath:\n            path: (".*")\n', read(tmp, 'dev/deployment.yaml'))
    is_ok(os.path.realpath(json.loads(path[1])) if path else None, os.path.realpath(tmp), 'host path')
    unlike_ok(read(tmp, 'dev/kustomization.yaml'), r'configMapGenerator', 'no ConfigMap')
    ok(not os.path.exists(tmp.child('kubernetes', 'dev', 'files')), 'no copy of the application')
    like_ok(
        read(tmp, 'dev/deployment.yaml'),
        r'exec /uv/venv/bin/python -m Pyjo\.Server\.Reload -w Pyjoyment -w templates Pyjoyment/__main__\.py"',
        'reload of the package',
    )

    # python -m MyApp generate kubernetes --graceful-timeout 25
    tmp = project()
    generate(tmp, '--graceful-timeout', '25')
    like_ok(read(tmp, 'prod/deployment.yaml'), r'(?m)^      terminationGracePeriodSeconds: 35$', 'grace period')
    like_ok(
        read(tmp, 'prod/deployment.yaml'),
        r'(?m)^            - name: PYJO_GRACEFUL_TIMEOUT\n              value: "25"$',
        'graceful timeout',
    )

    # python -m MyApp generate kubernetes --no-dev
    tmp = project()
    generate(tmp, '--no-dev')
    like_ok(read(tmp, 'dev/deployment.yaml'), r'uv sync --no-install-project --no-dev &&', 'no group dev')

    # python -m MyApp generate kubernetes --server prefork -- --workers 2
    tmp = project()
    generate(tmp, '--server', 'prefork', '--', '--workers', '2')
    like_ok(read(tmp, 'dev/deployment.yaml'), r'exec /uv/venv/bin/python -m Pyjoyment prefork --workers 2"', 'prefork')

with subtest('Description'):
    application = Pyjoyment.new()
    kubernetes = Pyjoyment.Command.Author.generate.kubernetes.new(app=application)
    tmp = project()
    tmp.child('.hidden').spew('')
    tmp.child('MyApp').make_path().child('__init__.py').spew('pass\n')
    tmp.child('MyApp', '__pycache__').make_path().child('x.pyc').spew('')
    tmp.child('dist').make_path().child('function.zip').spew('')
    tmp.child('public').make_path().child('logo.png').spew(b'\x89PNG\x00\xff')
    output = generate(tmp)
    for name in ('base/kustomization.yaml', 'base/deployment.yaml', 'base/service.yaml'):
        ok(os.path.isfile(tmp.child('kubernetes', *name.split('/'))), name)
    for name in ('dev/kustomization.yaml', 'dev/deployment.yaml', 'prod/kustomization.yaml', 'prod/deployment.yaml'):
        ok(os.path.isfile(tmp.child('kubernetes', *name.split('/'))), name)

    # The port of PORT, which the Service exposes on the port 80
    like_ok(read(tmp, 'base/deployment.yaml'), r'- name: PORT\n              value: "3000"', 'port')
    like_ok(read(tmp, 'base/service.yaml'), r'port: 80\n      targetPort: http', 'Service')
    # The probes of the port without Pyjoyment.Plugin.Health
    for probe in ('startupProbe', 'livenessProbe', 'readinessProbe'):
        like_ok(
            read(tmp, 'base/deployment.yaml'), rf'{probe}:\n            tcpSocket:\n              port: http', probe
        )
    unlike_ok(read(tmp, 'base/deployment.yaml'), r'httpGet', 'no request without Health')
    like_ok(read(tmp, 'dev/deployment.yaml'), r'startupProbe:\n            failureThreshold: 300', 'start of dev')

    # The probes of Pyjoyment.Plugin.Health
    application.plugin('Health')
    probes = project()
    generate(probes)
    like_ok(
        read(probes, 'base/deployment.yaml'),
        r'startupProbe:\n            httpGet:\n              path: /livez',
        'startup',
    )
    like_ok(
        read(probes, 'base/deployment.yaml'),
        r'livenessProbe:\n            httpGet:\n              path: /livez',
        'liveness',
    )
    like_ok(
        read(probes, 'base/deployment.yaml'),
        r'readinessProbe:\n            httpGet:\n              path: /readyz',
        'readiness',
    )
    like_ok(read(probes, 'dev/deployment.yaml'), r'startupProbe:\n            failureThreshold: 300', 'start of dev')

    # prod, in the operating mode production, on the image of the name of the application
    like_ok(read(tmp, 'base/deployment.yaml'), r'image: pyjoyment\n          imagePullPolicy: IfNotPresent', 'image')
    like_ok(read(tmp, 'prod/deployment.yaml'), r'- name: PYJO_MODE\n              value: production', 'production')
    like_ok(read(tmp, 'prod/deployment.yaml'), r'(?m)^      terminationGracePeriodSeconds: 35$', 'grace period')
    unlike_ok(read(tmp, 'prod/deployment.yaml'), r'PYJO_GRACEFUL_TIMEOUT', 'graceful timeout of the server')
    like_ok(read(tmp, 'prod/deployment.yaml'), r'preStop:\n              sleep:\n                seconds: 5', 'preStop')

    # dev, on the image of uv, with the group dev and the server daemon in the operating mode development
    deployment = read(tmp, 'dev/deployment.yaml')
    like_ok(deployment, rf'image: ghcr\.io/astral-sh/uv:python{python}-trixie-slim', 'image of uv')
    like_ok(deployment, r'uv sync --no-install-project && exec /uv/venv/bin/python -m Pyjoyment daemon"', 'daemon')
    like_ok(deployment, r'- name: PYJO_MODE\n              value: development', 'development')
    like_ok(deployment, r'- name: UV_PROJECT_ENVIRONMENT\n              value: /uv/venv', 'environment')
    like_ok(deployment, r'command: \["sh", "-c", "cp -RL /files/\* /app"\]', 'copy of the ConfigMap')

    # The ConfigMap of a copy of the application, without hidden files, __pycache__, dist and kubernetes
    kustomization = read(tmp, 'dev/kustomization.yaml')
    like_ok(kustomization, r'"MyApp\.__init__\.py=files/MyApp/__init__\.py"', 'file of the application')
    like_ok(deployment, r'- key: MyApp\.__init__\.py\n                path: "MyApp/__init__\.py"', 'path of the file')
    like_ok(kustomization, r'"public\.logo\.png=files/public/logo\.png"', 'binary file')
    unlike_ok(kustomization, r'hidden|__pycache__|dist|kubernetes/', 'nothing else')
    is_ok(tmp.child('kubernetes', 'dev', 'files', 'public', 'logo.png').slurp(), b'\x89PNG\x00\xff', 'copy of the file')

    # A ConfigMap holds 1 MiB at most
    large = project()
    large.child('data.bin').spew(b'x' * (1024 * 1024))
    throws_ok(lambda: generate(large), re.compile(r'^The application is larger than a ConfigMap holds'), 'limit')

    # The files of base and prod are written once, the ones of dev anew each time
    tmp.child('kubernetes', 'base', 'service.yaml').spew('# edited\n')
    tmp.child('MyApp', 'new.py').spew('')
    tmp.child('public', 'logo.png').remove()
    output = generate(tmp, '--port', '8080')
    like_ok(output, r'\[exist\] .*base.service\.yaml', 'base exists')
    is_ok(read(tmp, 'base/service.yaml'), '# edited\n', 'base kept')
    like_ok(output, r'\[write\] .*dev.kustomization\.yaml', 'dev written')
    like_ok(read(tmp, 'dev/kustomization.yaml'), r'MyApp/new\.py', 'new file')
    unlike_ok(read(tmp, 'dev/kustomization.yaml'), r'logo', 'removed file')
    ok(not os.path.exists(tmp.child('kubernetes', 'dev', 'files', 'public', 'logo.png')), 'removed copy')

    # --host-path removes the copy
    generate(tmp, '--host-path')
    ok(not os.path.exists(tmp.child('kubernetes', 'dev', 'files')), 'no copy')

    # The servers of --server, with the options after "--"
    generate(tmp, '-s', 'reload', '--', '-v')
    like_ok(read(tmp, 'dev/deployment.yaml'), r'Pyjo\.Server\.Reload -w Pyjoyment -w templates -v Pyjoyment/', 'reload')
    generate(tmp, '--host-path', '--server', 'daemon', '--', '-l', 'http://*:3000')
    like_ok(read(tmp, 'dev/deployment.yaml'), r"-m Pyjoyment daemon -l 'http://\*:3000'\"", 'daemon')
    throws_ok(lambda: generate(tmp, '--server', 'hot'), re.compile(r'^Unknown server: hot'), 'unknown server')

    # The script of Pyjoyment.Lite, with the inline metadata of PEP 723
    tmp = Pyjo.File.tempdir()
    script(tmp, '# /// script\n# dependencies = ["Pyjoyment"]\n# ///\n')
    try:
        generate(tmp)
        deployment = read(tmp, 'dev/deployment.yaml')
        generate(tmp, '--host-path')
        reload = read(tmp, 'dev/deployment.yaml')
    finally:
        os.environ.pop('PYJO_EXE', None)
    like_ok(deployment, r'uv venv --allow-existing /uv/venv && uv sync --script myapp\.py --active', 'script')
    like_ok(deployment, r'exec /uv/venv/bin/python myapp\.py daemon"', 'daemon of the script')
    like_ok(deployment, r'- name: VIRTUAL_ENV\n              value: /uv/venv', 'environment of the script')
    like_ok(reload, r'exec /uv/venv/bin/python -m Pyjo\.Server\.Reload myapp\.py"', 'reload of the script')

    # A name of Kubernetes, in lower case, without "_"
    application.moniker = 'My_App'
    tmp = project()
    generate(tmp)
    like_ok(read(tmp, 'base/deployment.yaml'), r'(?m)^  name: my-app$', 'name')
    like_ok(read(tmp, 'base/deployment.yaml'), r'(?m)^          image: My_App$', 'name of the image')
    like_ok(read(tmp, 'dev/kustomization.yaml'), r'(?m)^  - name: my-app-files$', 'name of the ConfigMap')

with subtest('Kustomize'):
    if not kubectl:
        plan(skip_all='kubectl is not installed')
    application = Pyjoyment.new()
    application.plugin('Health')
    kubernetes = Pyjoyment.Command.Author.generate.kubernetes.new(app=application)
    tmp = project()
    tmp.child('MyApp').make_path().child('__init__.py').spew('pass\n')
    generate(tmp, '--image', 'ghcr.io/me/myapp:1.0')
    for overlay in ('dev', 'prod'):
        command = [str(kubectl), 'kustomize', tmp.child('kubernetes', overlay).to_str()]
        result = subprocess.run(command, capture_output=True, text=True)
        is_ok(result.returncode, 0, f'{overlay} builds')
        like_ok(result.stdout, r'selector:\n    matchLabels:\n      app\.kubernetes\.io/name: pyjoyment', 'selector')
    like_ok(result.stdout, r'image: ghcr\.io/me/myapp:1\.0', 'image of prod')
    result = subprocess.run(
        [str(kubectl), 'kustomize', tmp.child('kubernetes', 'dev').to_str()], capture_output=True, text=True
    )
    like_ok(result.stdout, r'(?m)^  name: pyjoyment-files-[a-z0-9]{10}$', 'ConfigMap with a hash')
    like_ok(result.stdout, r'configMap:\n          items:\n          - key: MyApp\.__init__\.py', 'items')
    like_ok(result.stdout, r'name: pyjoyment-files-[a-z0-9]{10}\n', 'volume of the ConfigMap with the hash')

done_testing()
