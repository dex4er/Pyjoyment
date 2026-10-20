"""
Pyjoyment.Command.Author.generate.pyproject - pyproject.toml generator command
==============================================================================
::

    Usage: APPLICATION generate pyproject [OPTIONS]

      ./myapp.py generate pyproject
      pyjo generate pyproject

    Options:
      -h, --help   Show this summary of available options

:mod:`Pyjoyment.Command.Author.generate.pyproject` generates
``pyproject.toml`` files for applications, with their dependencies and no
build system, as ``uv init --app`` does, so that ``uv sync`` installs the
dependencies without the application. The name of the project is the one of
the current directory, and where it has a directory ``t``, the dependency
group ``dev`` has pytest and pytest-xdist, which ``uv sync`` installs and
``generate dockerfile`` leaves out, ``testpaths`` of pytest names ``t`` and
``pythonpath`` the current directory, so that ``uv run pytest`` runs its test
scripts with :mod:`Pyjo.Test.pytest_plugin`, and its tests find the
application.

This is a core command, that means it is always enabled and its code a good
example for learning to build new commands, you're welcome to fork it.

See :mod:`Pyjoyment.Commands` for a list of commands that are available by
default.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Command::Author::generate::makefile
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Command/Author/generate/makefile.pm>`_ of
Mojolicious 9.49.

Classes
-------
"""

# Renamed from Mojolicious: generate pyproject, where Mojo has generate makefile, as the dependencies of a project of
# Python are in pyproject.toml, which uv reads

import Pyjo.File
import Pyjoyment.Command

from Pyjo.Util import extract_usage
from Pyjoyment.Command.version import _version  # pyright: ignore[reportPrivateUsage]

import os
import re


class Pyjoyment_Command_Author_generate_pyproject(Pyjoyment.Command.object):
    """
    :mod:`Pyjoyment.Command.Author.generate.pyproject` inherits all attributes
    and methods from :mod:`Pyjoyment.Command` and implements the following new
    ones.
    """

    description = 'Generate "pyproject.toml"'
    """::

        description = pyproject.description
        pyproject.description = 'Foo'

    Short description of this command, used for the command list.
    """

    usage = extract_usage()
    """::

        usage = pyproject.usage
        pyproject.usage = 'Foo'

    Usage information for this command, used for the help screen.
    """

    def run(self, *args: str) -> None:
        """::

            pyproject.run(*sys.argv[1:])

        Run this command.
        """
        # Not in Mojolicious: the name of the project, which Makefile.PL of Mojo leaves out
        name = re.sub(r'[^A-Za-z0-9._-]+', '-', Pyjo.File.path().to_abs().basename()).strip('-._') or 'myapp'
        # Not in Mojolicious: testpaths of pytest for the test scripts in t
        tests = os.path.isdir('t')
        self.render_to_rel_file(
            'pyproject', 'pyproject.toml', {'name': name, 'requirement': _requirement(), 'tests': tests}
        )


# Not in Mojolicious: the requirement of the dependency on Pyjoyment, with the version that generates the files
def _requirement() -> str:
    version = _version()
    return 'Pyjoyment' if version == 'n/a' else f'Pyjoyment>={version}'


new = Pyjoyment_Command_Author_generate_pyproject.new
object = Pyjoyment_Command_Author_generate_pyproject

__DATA__ = r"""
@@ pyproject
[project]
name = "<%= name %>"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["<%= requirement %>"]
% if tests:

[dependency-groups]
dev = ["pytest>=9", "pytest-xdist>=3"]

[tool.pytest.ini_options]
testpaths = ["t"]
pythonpath = ["."]
% end
"""
