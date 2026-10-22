# pyjo_fastcgi.py PORT LOCATION SCRIPT: Pyjo.App.FastCGI of the location, with the script, on Pyjo.Server.Daemon
import Pyjo.App.FastCGI
import Pyjo.Server.Daemon

import sys


port, location, script = sys.argv[1:4]
app = Pyjo.App.FastCGI.new(url=location, env={'SCRIPT_FILENAME': script})
Pyjo.Server.Daemon.new(app=app, listen=[f'http://127.0.0.1:{port}'], silent=True).run()
