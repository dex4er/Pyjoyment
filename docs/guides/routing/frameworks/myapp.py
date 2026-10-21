from Pyjoyment.Lite import *


# A WSGI and an ASGI application of their own modules, by the names that their servers take
plugin('Mount', {'/legacy': 'legacy:app'})
plugin('Mount', {'/api': 'api:app'})


@get('/')
def index(c):
    c.render(text='Hello from Pyjoyment!')


app.start()
