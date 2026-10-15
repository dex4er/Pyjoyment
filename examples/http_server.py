import Pyjo.Server.Daemon
import Pyjo.URL

from Pyjo.Loader import data_section
from Pyjo.Util import xml_escape

import sys


opts = {'address': '0.0.0.0', 'port': '3000'} | dict(a.split('=', 1) for a in sys.argv[1:])

listen = str(Pyjo.URL.new().set(scheme='http', host=opts['address'], port=opts['port']))

daemon = Pyjo.Server.Daemon.new(listen=[listen])
daemon.unsubscribe('request')


# Embedded template file
DATA = r"""
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
"""


@daemon.on
def request(daemon, tx):
    # Request
    method = tx.req.method
    path = tx.req.url.path

    # Template
    template = data_section(__name__, 'index.html.tpl')

    # Response
    tx.res.code = 200
    tx.res.headers.content_type = 'text/html; charset=utf-8'
    tx.res.body = template.format(method=xml_escape(method), path=xml_escape(str(path))).encode()

    # Resume transaction
    tx.resume()


daemon.run()
