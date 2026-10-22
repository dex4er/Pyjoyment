from Pyjoyment.Lite import *


# The ASGI application of hello_asgi.py, next to this script, under /asgi
plugin('Mount', {'/asgi': 'hello_asgi:app'})

get('/', {'text': 'I ♥ Pyjoyment!'})

app.start()
