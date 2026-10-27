"""
Pyjoyment.Command.Author.generate.lite_app - Lite app generator command
=======================================================================
::

    Usage: APPLICATION generate lite-app [OPTIONS] [NAME]

      pyjo generate lite-app
      pyjo generate lite-app foo.py

    Options:
      -h, --help   Show this summary of available options

:mod:`Pyjoyment.Command.Author.generate.lite_app` generate fully functional
:mod:`Pyjoyment.Lite` applications.

This is a core command, that means it is always enabled and its code a good
example for learning to build new commands, you're welcome to fork it.

See :mod:`Pyjoyment.Commands` for a list of commands that are available by
default.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Command::Author::generate::lite_app
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Command/Author/generate/lite_app.pm>`_ of
Mojolicious 9.49.

Classes
-------
"""

import Pyjoyment.Command

from Pyjo.Util import extract_usage


class Pyjoyment_Command_Author_generate_lite_app(Pyjoyment.Command.object):
    """
    :mod:`Pyjoyment.Command.Author.generate.lite_app` inherits all attributes
    and methods from :mod:`Pyjoyment.Command` and implements the following new
    ones.
    """

    description = 'Generate Pyjoyment.Lite application'
    """::

        description = app.description
        app.description = 'Foo'

    Short description of this command, used for the command list.
    """

    usage = extract_usage()
    """::

        usage = app.usage
        app.usage = 'Foo'

    Usage information for this command, used for the help screen.
    """

    def run(self, name: str | None = None, *args: str) -> None:
        """::

            app.run(*sys.argv[1:])

        Run this command.
        """
        name = name or 'myapp.py'
        self.render_to_rel_file('liteapp', name)
        self.chmod_rel_file(name, 0o744)


new = Pyjoyment_Command_Author_generate_lite_app.new
object = Pyjoyment_Command_Author_generate_lite_app

__DATA__ = r'''
@@ liteapp
#!/usr/bin/env python
"""
<% %>__DATA__

<% %>@@ index.html.ep
%% c.layout('default')
%% c.title('Welcome')
<h1>Welcome to the Pyjoyment real-time web framework!</h1>

<% %>@@ layouts/default.html.ep
<!DOCTYPE html>
<html>
  <head><title><%%= c.title() %></title></head>
  <body><%%= content() %></body>
</html>
"""

from Pyjoyment.Lite import *

%# Not in Mojolicious: the plugin Health, whose endpoints the probes of containers and orchestrators request
# Liveness and readiness for containers and orchestrators
plugin('Health')


@get('/')
def index(c):
    c.render(template='index')


app.start()
'''
