import asyncio
import sys

import tornado.httpserver
import tornado.netutil
import tornado.process
import tornado.web


class Hello(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Content-Type', 'text/html;charset=UTF-8')
        self.write('Your Pyjo is working!')


async def main(sockets):
    tornado.httpserver.HTTPServer(tornado.web.Application([('/', Hello)])).add_sockets(sockets)
    await asyncio.Event().wait()


# tornado_app.py PORT [WORKERS]: with WORKERS, the processes of fork_processes, which share the listen socket
sockets = tornado.netutil.bind_sockets(int(sys.argv[1]), address='127.0.0.1')
if sys.argv[2:]:
    tornado.process.fork_processes(int(sys.argv[2]))
asyncio.run(main(sockets))
