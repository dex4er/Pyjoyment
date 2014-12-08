"""
Pyjo.Parameters
"""

import Pyjo.Base.String

from Pyjo.Util import url_escape


# TODO stub
class Pyjo_Parameters(Pyjo.Base.String.object):

    _params = None
    _string = None

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            self._string = list(args[0])
        elif len(args) == 1 and isinstance(args[0], dict):
            self._params = [a for sublist in sorted(args[0].items()) for a in sublist]
        elif len(args) > 1:
            self._params = list(args)
        elif args:
            self._string = args[0]
        elif kwargs:
            self._params = [a for sublist in sorted(kwargs.items()) for a in sublist]
        else:
            self._string = ''

    def to_string(self):
        if self._string:
            return self._string
        elif self._params:
            return '&'.join([url_escape(str(p[0])) + '=' + url_escape(str(p[1])) for p in list(zip(self._params[::2], self._params[1::2]))])
        else:
            return ''


new = Pyjo_Parameters.new
object = Pyjo_Parameters  # @ReservedAssignment
