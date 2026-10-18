from Pyjoyment.Lite import *


@get('/')
def index(c):

    # Prepare body
    body = b'Hello World!'

    # Start writing directly with a drain callback
    def drain(c):
        nonlocal body
        chunk, body = body[:1], body[1:]
        if chunk:
            c.write(chunk, drain)
        else:
            c.finish()

    drain(c)


app.start()
