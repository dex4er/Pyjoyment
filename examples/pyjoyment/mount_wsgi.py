from Pyjoyment.Lite import *


# The WSGI application of hello_wsgi.py, next to this script, under /wsgi
plugin('Mount', {'/wsgi': 'hello_wsgi:app'})

get('/', {'text': 'I ♥ Pyjoyment!'})

app.start()
