"""
Pyjoyment.Command.Author.generate.lambda_zip - Lambda ZIP generator command
===========================================================================
::

    Usage: APPLICATION generate lambda-zip [OPTIONS]

      ./myapp.py generate lambda-zip
      python -m MyApp generate lambda-zip
      python -m MyApp generate lambda-zip --arch arm64
      python -m MyApp generate lambda-zip --python 3.15t
      python -m MyApp generate lambda-zip --no-layer

    Options:
      -a, --arch <name>        Architecture of the function, "arm64" or "x86_64",
                               defaults to "x86_64"
      -h, --help               Show this summary of available options
          --no-layer           Put Python into the ZIP of the function, without a
                               layer
      -p, --python <version>   Version of Python, as "3.14" or "3.15t" for the
                               free-threaded build, defaults to the version that
                               runs the generator

:mod:`Pyjoyment.Command.Author.generate.lambda_zip` generates the ZIP files
of an event function of AWS Lambda on a custom runtime, as
``provided.al2023``, in ``dist``: ``function.zip``, with the application, its
dependencies and the ``bootstrap`` that runs it, and ``python.zip``, a layer
with Python, which Lambda extracts in ``/opt``, so that the function runs on
any Python, as the free-threaded build or a version that the runtimes of
Python of Lambda do not have yet.

The ``bootstrap`` runs the script of the application, or its package, which
is the runtime of the function itself, as :mod:`Pyjoyment.Command.lambda`
detects, with the runtime client of :mod:`Pyjo.Server.Lambda`. A function
whose Function URL streams its responses has
``PYJO_LAMBDA_INVOKE_MODE=RESPONSE_STREAM`` in its environment, as
:attr:`Pyjo.Server.Lambda.Pyjo_Server_Lambda.invoke_mode` says.

The files are made with uv, which has to be on ``PATH``. Python is the build
of python-build-standalone that uv installs, for Linux with glibc and the
architecture of ``--arch``: the interpreter and its standard library,
without IDLE, Tkinter, turtledemo, ensurepip and pip, which a function does
not use. The dependencies are the ones of ``pyproject.toml``, which
:mod:`Pyjoyment.Command.Author.generate.pyproject` generates, locked with
``uv.lock`` if there is one, or the ones of the inline metadata of PEP 723 of
a :mod:`Pyjoyment.Lite` script that has it and no ``pyproject.toml``, locked
with its ``.lock`` file if there is one, with the wheels of Amazon Linux 2023,
``manylinux_2_34``. The application is the files of the current directory,
without hidden ones, ``__pycache__`` and ``dist``.

Python cannot write its bytecode in ``/var/task`` and ``/opt``, which are
read-only, so the generator compiles it with the Python of the same version
that uv finds or installs for the machine that it runs on, with the
invalidation mode ``unchecked-hash``, which Python uses without checking the
source. The files of the same input are the same, as the times in the ZIP are
fixed, so that a deployment that compares their hashes, as the one of
OpenTofu, changes only what has changed. Both are written anew each time.

With ``--no-layer``, Python is in ``function.zip``, in the directory
``python``, and the function needs no layer, at the cost of a larger ZIP for
each deployment.

This is a core command, that means it is always enabled and its code a good
example for learning to build new commands, you're welcome to fork it.

See :mod:`Pyjoyment.Commands` for a list of commands that are available by
default.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

It has no counterpart in Mojolicious.

Classes
-------
"""

import Pyjo.Exception
import Pyjo.File
import Pyjoyment.Command

from Pyjo.Util import extract_usage, getopt

import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import zipfile


# The architectures of Lambda and the machines of Linux
_MACHINES = {'arm64': 'aarch64', 'x86_64': 'x86_64'}

# The parts of the standard library that a function does not use
_UNUSED = ('ensurepip', 'idlelib', 'site-packages', 'tkinter', 'turtledemo')

# The requirements that uv exports, for uv pip install
_FORMAT = ('--format', 'requirements.txt', '-o')


class Pyjoyment_Command_Author_generate_lambda_zip(Pyjoyment.Command.object):
    """
    :mod:`Pyjoyment.Command.Author.generate.lambda_zip` inherits all
    attributes and methods from :mod:`Pyjoyment.Command` and implements the
    following new ones.
    """

    description = 'Generate ZIP files of AWS Lambda'
    """::

        description = lambda_zip.description
        lambda_zip.description = 'Foo'

    Short description of this command, used for the command list.
    """

    usage = extract_usage()
    """::

        usage = lambda_zip.usage
        lambda_zip.usage = 'Foo'

    Usage information for this command, used for the help screen.
    """

    def run(self, *args: str) -> None:
        """::

            lambda_zip.run(*sys.argv[1:])

        Run this command.
        """
        arguments = list(args)
        if not (opts := getopt(arguments, {'a|arch=s': None, 'no-layer': None, 'p|python=s': None})):
            raise Pyjo.Exception.new(self.usage)

        arch: str = opts.arch or 'x86_64'
        if (machine := _MACHINES.get(arch)) is None:
            raise Pyjo.Exception.new(f'Unknown architecture: {arch}')
        version: str = opts.python or f'{sys.version_info.major}.{sys.version_info.minor}'
        if not re.fullmatch(r'3\.\d+(?:\.\d+)?t?', version):
            raise Pyjo.Exception.new(f'Unknown version of Python: {version}')
        layer = not opts.no_layer

        # The script of Pyjoyment.Lite or the package of the application, and the dependencies of the inline metadata of
        # PEP 723 of the script, if it has them and there is no pyproject.toml, as generate dockerfile has them
        exe = os.environ.get('PYJO_EXE')
        script = Pyjo.File.path(exe).to_rel(self.app.home).to_str() if exe else None
        cmd = [script] if script else ['-m', type(self.app).__module__]
        project = os.path.isfile(self.rel_file('pyproject.toml')) or not exe or not _metadata(Pyjo.File.path(exe))

        # The Python of the machine that compiles the bytecode and gives the tags of the wheels, of the same version,
        # with the GIL unless the version is the free-threaded one, which uv does not take otherwise
        local = version if version.endswith('t') else f'{version}+gil'

        with Pyjo.File.tempdir() as tmp:
            # Python, the interpreter and its standard library, in the directory of its full version, which the variables
            # of its build name, and not the link of its minor version
            install = tmp.child('install')
            self._uv(
                'python', 'install', '--no-bin', '--install-dir', install, f'cpython-{version}-linux-{machine}-gnu'
            )
            home = next(p for p in sorted(os.listdir(install)) if re.match(r'cpython-\d+\.\d+\.\d+', p))
            # The layer, which Lambda extracts in /opt, with Python in its directory python
            python = tmp.child('layer', 'python')
            prefix = '/opt/python' if layer else '/var/task/python'
            interpreter = _python(install.child(home), python, prefix)

            # The dependencies, without the scripts of their packages, which run the Python of the machine, and the lock
            # of uv
            function = tmp.child('function').make_path()
            requirements = 'pyproject.toml'
            if project and os.path.isfile(self.rel_file('uv.lock')):
                requirements = tmp.child('requirements.txt').to_str()
                self._uv('export', '--frozen', '--no-dev', '--no-emit-project', '--no-hashes', *_FORMAT, requirements)
            elif not project:
                frozen = ['--frozen'] if os.path.isfile(self.rel_file(f'{script}.lock')) else []
                requirements = tmp.child('requirements.txt').to_str()
                self._uv('export', '--script', script or '', *frozen, '--no-hashes', *_FORMAT, requirements)
            platform = f'{machine}-manylinux_2_34'
            deps = tmp.child('deps')
            self._uv(
                'pip', 'install', '--target', deps, '--python', local, '--python-platform', platform, '-r', requirements
            )
            if os.path.isdir(deps):
                top = os.fspath(deps)
                shutil.copytree(
                    deps, function, dirs_exist_ok=True, ignore=lambda dir, _: ['.lock', 'bin'] if dir == top else []
                )

            # The application, and the bootstrap that runs it
            for file in Pyjo.File.path().list_tree().each():
                name = file.to_rel(Pyjo.File.path()).to_str().replace(os.sep, '/')
                if name.split('/')[0] != 'dist' and '__pycache__' not in name.split('/'):
                    destination = function.child(*name.split('/'))
                    destination.dirname().make_path()
                    shutil.copyfile(file.to_str(), destination.to_str())
            executable = f'{prefix}/bin/{interpreter}' if layer else f'"$LAMBDA_TASK_ROOT/python/bin/{interpreter}"'
            function.child('bootstrap').spew(
                self.render_data('bootstrap', {'cmd': shlex.join(cmd), 'python': executable})
            )

            # The bytecode, as /var/task and /opt are read-only
            self._compile(local, python, prefix)
            self._compile(local, function, '/var/task')

            dist = self.rel_file('dist')
            self.create_dir(dist)
            if layer:
                _zip(python.dirname(), dist.child('python.zip'), {f'python/bin/{interpreter}'})
                self._loud(f'  [write] {dist.child("python.zip")}')
            else:
                shutil.copytree(python, function.child('python'))
            _zip(function, dist.child('function.zip'), {'bootstrap', f'python/bin/{interpreter}'})
            self._loud(f'  [write] {dist.child("function.zip")}')

    # The bytecode of a set of strings, as in "x in {'a', 'b'}", has the order of their hashes, which a fixed seed keeps
    def _compile(self, local: str, dir: Pyjo.File.object, prefix: str) -> None:
        options = ['-q', '-j', '0', '--invalidation-mode', 'unchecked-hash', '-s', dir.to_str(), '-p', prefix]
        env = {**os.environ, 'PYTHONHASHSEED': '0'}
        self._uv('run', '--no-project', '--python', local, '--', 'python', '-m', 'compileall', *options, dir, env=env)

    def _uv(self, *args: str | Pyjo.File.object, env: dict[str, str] | None = None) -> None:
        command = [*_uv(), '--quiet', *map(str, args)]
        if (code := subprocess.run(command, env=env).returncode) != 0:
            raise Pyjo.Exception.new(f'Command "uv {" ".join(map(str, args[:2]))}" failed with exit status {code}')


# The interpreter and its standard library, without what a function does not use, with the prefix of Python on Lambda in
# the variables of the build, where uv puts the directory that it installs in, and the name of the interpreter
def _python(home: Pyjo.File.object, python: Pyjo.File.object, prefix: str) -> str:
    bin = home.child('bin')
    names = sorted(os.listdir(bin))
    interpreter = next(n for n in names if re.fullmatch(r'python3\.\d+t?', n) and not os.path.islink(bin.child(n)))
    python.child('bin').make_path()
    shutil.copyfile(bin.child(interpreter).to_str(), python.child('bin', interpreter).to_str())
    library = python.child('lib', interpreter)
    shutil.copytree(home.child('lib', interpreter), library, symlinks=True)
    for name in os.listdir(library):
        if name in _UNUSED or name.startswith('config-'):
            shutil.rmtree(library.child(name))
        elif name.startswith('_sysconfigdata_') and name.endswith('.py'):
            data = library.child(name)
            data.spew(str(data.slurp('UTF-8')).replace(home.to_str(), prefix), 'UTF-8')
    for name in os.listdir(library.child('lib-dynload')):
        if name.startswith('_tkinter'):
            os.remove(library.child('lib-dynload', name))
    return interpreter


# Whether the script has the inline metadata of PEP 723
def _metadata(path: Pyjo.File.object) -> bool:
    try:
        return re.search(r'(?m)^# /// script\r?$', str(path.slurp('UTF-8') or '')) is not None
    except OSError:
        return False


# The command of uv
def _uv() -> list[str]:
    if (uv := shutil.which('uv')) is None:
        raise Pyjo.Exception.new('Command "uv" not found')
    return [uv]


# A ZIP file of the directory, the same for the same files, with the modes of Lambda, which the files of Windows do not
# have, and without the symbolic links of Python, which the interpreter does not need
def _zip(dir: Pyjo.File.object, path: Pyjo.File.object, executables: set[str]) -> None:
    with zipfile.ZipFile(path.to_str(), 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in dir.list_tree(hidden=True).each():
            if os.path.islink(file):
                continue
            name = file.to_rel(dir).to_str().replace(os.sep, '/')
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | (0o755 if name in executables else 0o644)) << 16
            with open(file, 'rb') as source, archive.open(info, 'w') as destination:
                shutil.copyfileobj(source, destination)


new = Pyjoyment_Command_Author_generate_lambda_zip.new
object = Pyjoyment_Command_Author_generate_lambda_zip

__DATA__ = r"""
@@ bootstrap
#!/bin/sh
# The runtime of the event function: the application, with the runtime client of Pyjo.Server.Lambda
cd "$LAMBDA_TASK_ROOT" || exit 1
exec <%= python %> <%= cmd %>
"""
