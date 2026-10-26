import Pyjo.JSON

from Pyjoyment.Lite import *

import re


# Public data, as any site can read them
HEADLINES = {'headlines': ['Pyjoyment released', 'Hello World!']}

# A name of JavaScript, with dots for the members of an object
CALLBACK = re.compile(r'[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*')


@get('/headlines')
def headlines(c):
    callback = c.param('callback') or ''
    if not CALLBACK.fullmatch(callback):
        return c.render(text='Invalid callback', status=400)
    c.res.headers.header('X-Content-Type-Options', 'nosniff')
    c.render(text=f'/**/{callback}({Pyjo.JSON.to_json(HEADLINES)});', format='js')


app.start()
