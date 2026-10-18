from Pyjoyment.Lite import *


@get('/')
def index(c):

    # Prepare body
    body = b'Hello World!'
    c.res.headers.content_length = len(body)

    # Start writing directly with a drain callback
    def drain(c):
        nonlocal body
        chunk, body = body[:1], body[1:]
        c.write(chunk, drain if body else None)

    drain(c)


app.start()
