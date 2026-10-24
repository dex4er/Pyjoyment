from Pyjoyment.Lite import *


# Every host for the pages, only the ones of localhost for the endpoint of MCP
plugin('AllowedHosts', hook=False)


@get('/')
def index(c):
    c.render(text='Hello World!')


with group():
    under('/mcp', lambda c: c.allowed_hosts())

    @post('/')
    def mcp(c):
        c.render(json={'jsonrpc': '2.0', 'id': 1, 'result': {}})


app.start()
