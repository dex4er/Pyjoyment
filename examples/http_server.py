import Pyjo.Server.Daemon
import Pyjo.Template
import Pyjo.URL

from Pyjo.Loader import data_section

import sys


opts = {'address': '0.0.0.0', 'port': '3000'} | dict(a.split('=', 1) for a in sys.argv[1:])

listen = str(Pyjo.URL.new().set(scheme='http', host=opts['address'], port=opts['port']))

daemon = Pyjo.Server.Daemon.new(listen=[listen])
daemon.unsubscribe('request')


# Embedded template file
__DATA__ = r"""
@@ index.html.ep
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Pyjoyment</title>
</head>
<body>
<h1>♥ Pyjoyment ♥</h1>
<h2>This page is served by Pyjoyment framework.</h2>
<p><%= method %> request for <%= path %></p>
</body>
</html>
"""

template = Pyjo.Template.new(auto_escape=True, vars=True).parse(data_section(__name__, 'index.html.ep'))


@daemon.on
def request(daemon, tx):
    # Request
    method = tx.req.method
    path = tx.req.url.path

    # Response
    tx.res.code = 200
    tx.res.headers.content_type = 'text/html; charset=utf-8'
    tx.res.body = template.process({'method': method, 'path': path}).encode()

    # Resume transaction
    tx.resume()


daemon.run()
