"""
__DATA__

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

import Pyjo.App
import Pyjo.GetOpt
import Pyjo.Server.Daemon
import Pyjo.Template
import Pyjo.URL

from Pyjo.Loader import data_section
from Pyjo.Util import die


class MyApp(Pyjo.App.object):
    # Embedded template file
    template = Pyjo.Template.new(auto_escape=True, vars=True).parse(data_section(__name__, 'index.html.ep'))

    # All the complexities of CGI, WSGI, ASGI, HTTP and WebSockets get reduced to a single method call!
    def handler(self, tx):
        # Resume transaction at the end of the block
        with tx:
            # Request
            method = tx.req.method
            path = tx.req.url.path

            # Response
            tx.res.code = 200
            tx.res.headers.content_type = 'text/html; charset=utf-8'
            tx.res.body = self.template.process({'method': method, 'path': path}).encode()


# Options --address and --port
getopt = Pyjo.GetOpt.new().option('a|address=s', default='0.0.0.0').option('p|port=i', default=3000)
opts = getopt.parse() or die('Usage: http_server.py [--address ADDRESS] [--port PORT]')

url = Pyjo.URL.new().set(scheme='http', host=opts.address, port=opts.port)

Pyjo.Server.Daemon.new(app=MyApp.new(), listen=[url]).run()
