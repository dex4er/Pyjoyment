import asyncio
import sys

import tornado.web


class Hello(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Content-Type', 'text/html;charset=UTF-8')
        self.write('Your Pyjo is working!')


async def main():
    tornado.web.Application([('/', Hello)]).listen(int(sys.argv[1]), address='127.0.0.1')
    await asyncio.Event().wait()


asyncio.run(main())
