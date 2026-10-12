import Pyjo.Server.Daemon
import Pyjo.URL

from Pyjo.Loader import embedded_file
from Pyjo.Util import b, u

import sys


opts = dict([['address', '0.0.0.0'], ['port', 3000]] + list(map(lambda a: a.split('='), sys.argv[1:])))

listen = str(Pyjo.URL.new(scheme='http', host=opts['address'], port=opts['port']))

daemon = Pyjo.Server.Daemon.new(listen=[listen])
daemon.unsubscribe('request')


# Embedded template file
DATA = u(r"""
@@ index.html.tpl
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Pyjoyment</title>
</head>
<body>
<h1>♥ Pyjoyment ♥</h1>
<h2>This page is served by Pyjoyment framework.</h2>
<p>{method} request for {path}</p>
</body>
</html>
""")


@daemon.on
def request(daemon, tx):
    # Request
    method = tx.req.method
    path = tx.req.url.path

    # Template
    template = embedded_file(sys.modules[__name__], 'index.html.tpl')

    # Response
    tx.res.code = 200
    tx.res.headers.content_type = 'text/html; charset=utf-8'
    tx.res.body = b(template.format(**locals()))

    # Resume transaction
    tx.resume()


daemon.run()
