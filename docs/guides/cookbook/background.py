import Pyjo.IOLoop

from Pyjoyment.Lite import *


# Check title in the background every 10 seconds
title = 'Got no title yet.'


@Pyjo.IOLoop.recurring(10)
def check(loop):
    def update(ua, tx):
        global title
        title = tx.result.dom().at('title').text

    app.ua.get('https://pyjoyment.readthedocs.io', update)


# Show current title
@get('/')
def index(c):
    c.render(json={'title': title})


app.start()
