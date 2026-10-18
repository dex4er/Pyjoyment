from Pyjoyment.Lite import *


# Just forward the response
@get('/')
def index(c):
    @c.proxy.get_p('https://pyjoyment.readthedocs.io').catch
    def error(err):
        c.log().error(f'Proxy error: {err}')
        c.render(text='Could not connect to backend web service!', status=400)


# Forward response and customize a few things
@get('/*docs')
def docs(c):
    # Custom request
    tx = c.ua().build_tx('GET', 'https://pyjoyment.readthedocs.io')
    docs = c.param('docs')
    tx.req.url.path = f'/{docs}'
    tx.req.headers.user_agent = 'PyjoProxy/1.0'

    # Start non-blocking request
    @c.proxy.start_p(tx).catch
    def error(err):
        c.log().error(f'Proxy error: {err}')
        c.render(text='Could not connect to backend web service!', status=400)

    # Custom response
    @tx.res.content.once('body')
    def body(content):
        c.res.headers.server = 'PyjoProxy/1.0'


app.start()
