"""
Pyjoyment.Command.Author - Author commands
==========================================

``Pyjoyment.Command.Author`` is the namespace of the commands for the authors
of applications and plugins, as :mod:`Pyjoyment.Command.Author.generate` and
:mod:`Pyjoyment.Command.Author.inflate`, which :mod:`Pyjoyment.Commands`
loads before the ones of ``Pyjoyment.Command``.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.
"""

from pkgutil import extend_path


# Not in Mojolicious: a namespace that other distributions can add commands to
__path__ = extend_path(__path__, __name__)
