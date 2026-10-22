import Pyjo.App.CGI

from Pyjo.File import curfile
from Pyjoyment.Lite import *


# The programs of the directory cgi-bin, next to this script, under /cgi-bin, a process for each request
plugin('Mount', {'/cgi-bin': Pyjo.App.CGI.new(document_root=curfile().sibling('cgi-bin').to_str())})

get('/', {'text': 'I ♥ Pyjoyment!'})

app.start()
