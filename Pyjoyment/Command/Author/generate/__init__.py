"""
Pyjoyment.Command.Author.generate - Generator command
=====================================================
::

    Usage: APPLICATION generate GENERATOR [OPTIONS]

      pyjo generate app
      pyjo generate lite-app

:mod:`Pyjoyment.Command.Author.generate` lists available generators.

This is a core command, that means it is always enabled and its code a good
example for learning to build new commands, you're welcome to fork it.

See :mod:`Pyjoyment.Commands` for a list of commands that are available by
default.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Command::Author::generate
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Command/Author/generate.pm>`_ of Mojolicious 9.49.

Classes
-------
"""

import Pyjoyment.Commands

from pkgutil import extend_path
from typing import Any


class Pyjoyment_Command_Author_generate(Pyjoyment.Commands.object):
    """
    :mod:`Pyjoyment.Command.Author.generate` inherits all attributes and
    methods from :mod:`Pyjoyment.Commands` and implements the following new
    ones.
    """

    description = 'Generate files and directories from templates'
    """::

        description = generator.description
        generator.description = 'Foo'

    Short description of this command, used for the command list.
    """

    hint = "\nSee 'APPLICATION generate help GENERATOR' for more information on a specific\ngenerator.\n"
    """::

        hint = generator.hint
        generator.hint = 'Foo'

    Short hint shown after listing available generator commands.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if 'namespaces' not in kwargs:
            self.namespaces = ['Pyjoyment.Command.Author.generate']
            """::

                namespaces = generator.namespaces
                generator.namespaces = ['MyApp.Command.generate']

            Namespaces to search for available generator commands, defaults to
            ``Pyjoyment.Command.Author.generate``.
            """

    @property
    def message(self) -> str:
        """::

            msg = generator.message
            generator.message = 'Bar'

        Short usage message shown before listing available generator commands.
        """
        if self._message is None:
            self._message = self.extract_usage() + '\nGenerators:\n'
        return self._message

    @message.setter
    def message(self, value: str) -> None:
        self._message = value

    def help(self, *args: str) -> Any:
        """::

            generator.help('app')

        Print usage information for generator command.
        """
        return self.run(*args)


# Not in Mojolicious: a namespace that other distributions can add generators to
__path__ = extend_path(__path__, __name__)

new = Pyjoyment_Command_Author_generate.new
object = Pyjoyment_Command_Author_generate
