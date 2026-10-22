import Pyjo.App.CGI

from Pyjo.File import curfile
from Pyjoyment.Lite import *


# The scripts of PHP of the directory php under /php, on php-cgi of PATH, a process for each request
cgi = Pyjo.App.CGI.new(command=['php-cgi'], document_root=curfile().sibling('php').to_str(), script_extensions=['.php'])
plugin('Mount', {'/php': cgi})

get('/', {'text': 'I ♥ Pyjoyment!'})

app.start()
