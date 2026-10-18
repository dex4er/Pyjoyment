from Pyjoyment.Lite import *


# Request HTML titles from two sites non-blocking
@get('/')
async def index(c):
    pyjo_tx = await c.ua().get_p('https://pyjoyment.readthedocs.io')
    pyjo_title = pyjo_tx.result.dom().at('title').text
    mojo_tx = await c.ua().get_p('https://mojolicious.org')
    mojo_title = mojo_tx.result.dom().at('title').text

    c.render(json={'pyjo': pyjo_title, 'mojo': mojo_title})


app.start()
