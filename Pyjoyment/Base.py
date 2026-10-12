
"""
Pyjoyment.Base - Base class for Pyjoyment applications
======================================================
::

    import Pyjoyment.Base

    class MyApp(Pyjoyment.Base.object):
        ...
"""


import Pyjo.Base


class Pyjoyment_Base(Pyjo.Base.object):
    def start(self, *args):
        pass


new = Pyjoyment_Base.new
object = Pyjoyment_Base
