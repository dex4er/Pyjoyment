"""
Pyjoyment.Command.Author.generate.dockerfile - Dockerfile generator command
===========================================================================
::

    Usage: APPLICATION generate dockerfile [OPTIONS]

      ./myapp.py generate dockerfile
      python -m MyApp generate dockerfile
      python -m MyApp generate dockerfile --user app
      python -m MyApp generate dockerfile --port 8080

    Options:
      -h, --help          Show this summary of available options
      -p, --port <port>   Port that the server listens on and the image
                          exposes, defaults to 3000
      -u, --user <name>   Create a system user and run the application as it,
                          defaults to the user of the image

:mod:`Pyjoyment.Command.Author.generate.dockerfile` generates ``Dockerfile``
and ``.dockerignore`` for applications.

The image is built in two stages. The first one installs the dependencies
with uv into ``.venv``: the ones of ``pyproject.toml``, which
:mod:`Pyjoyment.Command.Author.generate.pyproject` generates, locked with
``uv.lock`` if there is one, or the ones of the inline metadata of PEP 723 of
a :mod:`Pyjoyment.Lite` script that has it and no ``pyproject.toml``, locked
with its ``.lock`` file if there is one. The second one has Python, ``.venv``
and the application only, and its command runs the pre-forking server without
uv, so that the signals of ``docker stop`` go straight to the server, which
stops gracefully on ``TERM``. The images of Python and of uv are those of the
versions that run the generator.

Docker gives a container 10 seconds to stop, less than the 25 seconds that
:attr:`Pyjo.Server.Prefork.Pyjo_Server_Prefork.graceful_timeout` gives a
worker, so ``docker stop -t 30``, or ``stop_grace_period: 30s`` of Docker
Compose, lets the workers finish their requests.

The server listens on the port of the ``PORT`` environment variable, which
the image sets to the port of ``--port``, ``3000`` by default, and exposes,
and which ``docker build --build-arg PORT=8080`` changes too. A platform as
Knative, Cloud Run, Render, Koyeb or Heroku sets ``PORT`` for the container,
and the server listens on its port, as Knative ignores ``EXPOSE`` and sets
``PORT`` to the ``containerPort`` of the service, ``8080`` by default.

This is a core command, that means it is always enabled and its code a good
example for learning to build new commands, you're welcome to fork it.

See :mod:`Pyjoyment.Commands` for a list of commands that are available by
default.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Command::Author::generate::dockerfile
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Command/Author/generate/dockerfile.pm>`_ of
Mojolicious 9.49.

Classes
-------
"""

import Pyjo.Exception
import Pyjo.File
import Pyjoyment.Command

from Pyjo.Util import extract_usage, getopt

import json
import os
import re
import shutil
import subprocess
import sys


class Pyjoyment_Command_Author_generate_dockerfile(Pyjoyment.Command.object):
    """
    :mod:`Pyjoyment.Command.Author.generate.dockerfile` inherits all
    attributes and methods from :mod:`Pyjoyment.Command` and implements the
    following new ones.
    """

    description = 'Generate "Dockerfile"'
    """::

        description = dockerfile.description
        dockerfile.description = 'Foo'

    Short description of this command, used for the command list.
    """

    usage = extract_usage()
    """::

        usage = dockerfile.usage
        dockerfile.usage = 'Foo'

    Usage information for this command, used for the help screen.
    """

    def run(self, *args: str) -> None:
        """::

            dockerfile.run(*sys.argv[1:])

        Run this command.
        """
        # Not in Mojolicious: the options
        arguments = list(args)
        if not (opts := getopt(arguments, {'p|port=i': None, 'u|user=s': None})):
            raise Pyjo.Exception.new(self.usage)

        name = self.app.moniker

        # Unlike Mojolicious: the script of Pyjoyment.Lite or the package of the application, which python runs, where
        # Mojo runs the script, and the dependencies of the inline metadata of PEP 723 of the script, if it has them and
        # there is no pyproject.toml
        exe = os.environ.get('PYJO_EXE')
        script = Pyjo.File.path(exe).to_rel(self.app.home).to_str() if exe else None
        cmd = ['python', script] if script else ['python', '-m', type(self.app).__module__]
        project = os.path.isfile(self.rel_file('pyproject.toml')) or not exe or not _metadata(Pyjo.File.path(exe))
        lock = 'uv.lock' if project else f'{script}.lock'
        values = {
            'cmd': json.dumps([*cmd, 'prefork']),
            'lock': lock if os.path.isfile(self.rel_file(lock)) else None,
            'name': name,
            'port': opts.port or 3000,
            'python': f'{sys.version_info.major}.{sys.version_info.minor}',
            'script': None if project else script,
            'user': opts.user,
            'uv': _uv(),
        }
        self.render_to_rel_file('dockerfile', 'Dockerfile', values)

        # Not in Mojolicious: .dockerignore, as the .venv of the host is not the one of the image
        self.render_to_rel_file('dockerignore', '.dockerignore')


# Not in Mojolicious: whether the script has the inline metadata of PEP 723
def _metadata(path: Pyjo.File.object) -> bool:
    try:
        return re.search(r'(?m)^# /// script\r?$', str(path.slurp('UTF-8') or '')) is not None
    except OSError:
        return False


# Not in Mojolicious: the version of uv, for its image
def _uv() -> str:
    if (uv := shutil.which('uv')) is None:
        return 'latest'
    try:
        output = subprocess.run([uv, '--version'], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return 'latest'
    return m[1] if (m := re.match(r'uv (\d+\.\d+\.\d+)', output)) else 'latest'


new = Pyjoyment_Command_Author_generate_dockerfile.new
object = Pyjoyment_Command_Author_generate_dockerfile

__DATA__ = r"""
@@ dockerfile
FROM python:<%= python %>-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:<%= uv %> /uv /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_DEV=1 UV_PYTHON_DOWNLOADS=0
WORKDIR /opt/<%= name %>
% if script:
ENV VIRTUAL_ENV=/opt/<%= name %>/.venv
COPY <%= ' '.join([script, *([lock] if lock else [])]) %> ./
RUN uv venv && uv sync --script <%= script %> --active<%= ' --locked' if lock else '' %>
% else:
COPY <%= ' '.join(['pyproject.toml', *([lock] if lock else [])]) %> ./
RUN uv sync --no-install-project<%= ' --locked' if lock else '' %>
% end

FROM python:<%= python %>-slim
WORKDIR /opt/<%= name %>
COPY --from=builder /opt/<%= name %>/.venv .venv
COPY . .
ENV PATH="/opt/<%= name %>/.venv/bin:$PATH"
% if user:
RUN useradd --system <%= user %>
USER <%= user %>
% end
ARG PORT=<%= port %>
ENV PORT=${PORT}
EXPOSE ${PORT}
CMD <%= cmd %>

@@ dockerignore
.git
.venv
__pycache__
"""
