#!/usr/bin/env python
"""
__DATA__

@@ menubar.html.ep
%= same_name()
%= stash('message') or 'works 4!'
"""

import Pyjo.IOLoop

from Pyjoyment.Lite import app, get, helper, hook


# Default for config file tests
app.defaults(secret='Insecure too!')

# Helpers sharing the same name in different embedded applications
helper('same_name', lambda c: 'myapp2')

# Caching helper for state variable test
cache = []


@helper('my_cache')
def my_cache(c):
    if not cache:
        cache.append(c.param('cache'))
    return cache[0]


# Delay dispatching
@hook('around_dispatch')
def around_dispatch(next, c):
    Pyjo.IOLoop.next_tick(lambda loop: next())


@get('/')
def index(c):
    c.render(text=str(c.render_to_string('menubar')) + app.defaults()['secret'])


@get('/cached')
def cached(c):
    c.render(text=c.my_cache())


app.start()
