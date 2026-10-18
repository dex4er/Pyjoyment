"""
Pyjoyment.Command.lambda - AWS Lambda command
=============================================
::

    Usage: APPLICATION lambda [OPTIONS]

      handler = app.start('lambda')

    Options:
      -h, --help          Show this summary of available options
          --home <path>   Path to home directory of your application, defaults to
                          the value of PYJO_HOME or auto-detection
      -m, --mode <name>   Operating mode for your application, defaults to the
                          value of PYJO_MODE or "development"

:mod:`Pyjoyment.Command.lambda` starts applications with the
:mod:`Pyjo.Server.Lambda` backend: it returns the handler of an event
function of AWS Lambda, which a script keeps for the runtime that imports it.
The script of an application that ends with ``handler = app.start()``, as
``myapp.py`` with the handler ``myapp.handler``, runs this command in the
runtime of AWS Lambda, which has the ``AWS_LAMBDA_RUNTIME_API`` environment
variable, and the command of its arguments otherwise.

This is a core command, that means it is always enabled and its code a good
example for learning to build new commands, you're welcome to fork it.

See :mod:`Pyjoyment.Commands` for a list of commands that are available by
default.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Classes
-------
"""

# Not in Mojolicious: the command of AWS Lambda, as Pyjoyment.Command.wsgi is the one of WSGI; its module has the name
# of a keyword of Python, which only the loader of the commands imports

import Pyjo.Server.Lambda
import Pyjoyment.Command

from Pyjo.Util import extract_usage

from typing import Any


class Pyjoyment_Command_lambda(Pyjoyment.Command.object):
    """
    :mod:`Pyjoyment.Command.lambda` inherits all attributes and methods from
    :mod:`Pyjoyment.Command` and implements the following new ones.
    """

    description = 'Start application with AWS Lambda'
    """::

        description = command.description
        command.description = 'Foo'

    Short description of this command, used for the command list.
    """

    usage = extract_usage()
    """::

        usage = command.usage
        command.usage = 'Foo'

    Usage information for this command, used for the help screen.
    """

    def run(self, *args: str) -> Any:
        """::

            handler = command.run()

        Run this command.
        """
        return Pyjo.Server.Lambda.new(app=self.app).to_lambda_app()


new = Pyjoyment_Command_lambda.new
object = Pyjoyment_Command_lambda
