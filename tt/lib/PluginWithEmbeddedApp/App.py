"""
__DATA__
@@ foo.html.ep
plugin works!\\
"""

from Pyjoyment.Lite import app, get


__all__ = ['app']

get('/foo')
