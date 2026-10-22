import Pyjo.IOLoop

from Pyjoyment.Lite import *


# The lines of the body sorted by the program sort, streamed as they come
@post('/sort')
def sort(c):
    c.render_later()
    child = Pyjo.IOLoop.spawn(['sort'])

    @child.on('spawn')
    def spawn(child):
        child.stdout.on('read', lambda stream, chunk: c.write_chunk(chunk))
        child.stdin.write(c.req.body).close_gracefully()

    child.on('close', lambda child, code, signal: c.write_chunk(b''))
    child.on('error', lambda child, err: c.reply.exception(err))


app.start()
