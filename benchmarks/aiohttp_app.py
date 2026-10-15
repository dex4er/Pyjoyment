import sys

from aiohttp import web


async def hello(request):
    return web.Response(text='Your Pyjo is working!', content_type='text/html')


app = web.Application()
app.router.add_get('/', hello)
web.run_app(app, host='127.0.0.1', port=int(sys.argv[1]))
