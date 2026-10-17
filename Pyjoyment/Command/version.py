"""
Pyjoyment.Command.version - Version command
===========================================
::

    Usage: APPLICATION version [OPTIONS]

      pyjo version

    Options:
      -h, --help   Show this summary of available options

:mod:`Pyjoyment.Command.version` shows version information for
available core and optional modules.

This is a core command, that means it is always enabled and its code a good
example for learning to build new commands, you're welcome to fork it.

See :mod:`Pyjoyment.Commands` for a list of commands that are available by
default.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Command::version
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Command/version.pm>`_ of Mojolicious 9.49.

Classes
-------
"""

import Pyjo.IOLoop.Client
import Pyjo.IOLoop.TLS
import Pyjo.Reactor
import Pyjoyment.Command

from Pyjo.Util import extract_usage

import importlib.metadata
import platform
import re
import ssl
import sys
import tomllib

from pathlib import Path
from typing import Any


class Pyjoyment_Command_version(Pyjoyment.Command.object):
    """
    :mod:`Pyjoyment.Command.version` inherits all attributes and methods from
    :mod:`Pyjoyment.Command` and implements the following new ones.
    """

    description = 'Show versions of available modules'
    """::

        description = version.description
        version.description = 'Foo'

    Short description of this command, used for the command list.
    """

    usage = extract_usage()
    """::

        usage = version.usage
        version.usage = 'Foo'

    Usage information for this command, used for the help screen.
    """

    def run(self, *args: str) -> None:
        """::

            version.run(*sys.argv[1:])

        Run this command.
        """
        # Unlike Mojolicious: the counterparts of the optional modules of Perl that Mojo shows, which Python has in its
        # standard library, and which Pyjoyment can turn off
        reactor = Pyjo.Reactor.detect()
        nnr = 'getaddrinfo in a thread' if Pyjo.IOLoop.Client.object.can_nnr() else 'n/a'
        socks = 'Pyjo.IOLoop.Client' if Pyjo.IOLoop.Client.object.can_socks() else 'n/a'
        tls = ssl.OPENSSL_VERSION if Pyjo.IOLoop.TLS.object.can_tls() else 'n/a'
        current = _version()

        print(f"""CORE
  Python     ({platform.python_version()}, {sys.platform})
  Pyjoyment  ({current})

OPTIONAL
  Reactor    ({reactor})
  NNR        ({nnr})
  SOCKS5     ({socks})
  TLS        ({tls})
""")

        # Check latest version on PyPI
        # Unlike Mojolicious: the JSON API of PyPI, where Mojo asks MetaCPAN
        try:
            ua = self.app.ua
            ua.max_redirects = 10
            ua.proxy.detect()
            latest = str(ua.get('https://pypi.org/pypi/Pyjoyment/json').result.json()['info']['version'])
        except Exception:
            return

        msg = 'This version is up to date, have fun!'
        if _numbers(latest) < _numbers(current):
            msg = 'Thanks for testing a development release, you are awesome!'
        if _numbers(latest) > _numbers(current):
            msg = f'You might want to update your Pyjoyment to {latest}!'
        print(msg)


# The numbers of a version, which compare as the versions do
def _numbers(version: str) -> tuple[int, ...]:
    return tuple(int(number) for number in re.findall(r'\d+', version))


# Not in Mojolicious: the version of the distribution, from its metadata, or from the pyproject.toml of a checkout of
# its source, as Python has no $VERSION of a module
def _version() -> str:
    try:
        return importlib.metadata.version('Pyjoyment')
    except importlib.metadata.PackageNotFoundError:
        pass
    pyproject = Path(__file__).resolve().parents[2] / 'pyproject.toml'
    try:
        project: Any = tomllib.loads(pyproject.read_text(encoding='utf-8')).get('project', {})
    except (OSError, tomllib.TOMLDecodeError):
        return 'n/a'
    return str(project['version']) if project.get('name') == 'Pyjoyment' and 'version' in project else 'n/a'


new = Pyjoyment_Command_version.new
object = Pyjoyment_Command_version
