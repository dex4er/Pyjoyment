import Pyjo.Server.Prefork
import Pyjo.Server.Prethread
import Pyjoyment.HelloWorld

import os
import sys
import tempfile


# pyjo_workers.py prefork|prethread PORT WORKERS [pyjoyment]: Pyjo.HelloWorld, or Pyjoyment.HelloWorld, on a server of
# workers, with a process id file of its own for each port
server, port, workers = sys.argv[1], sys.argv[2], int(sys.argv[3])
module = Pyjo.Server.Prethread if server == 'prethread' else Pyjo.Server.Prefork
options = {'app': Pyjoyment.HelloWorld.new()} if sys.argv[4:] == ['pyjoyment'] else {}
module.new(
    listen=[f'http://127.0.0.1:{port}'],
    pid_file=os.path.join(tempfile.gettempdir(), f'pyjo-workers-{port}.pid'),
    silent=True,
    workers=workers,
    **options,
).run()
