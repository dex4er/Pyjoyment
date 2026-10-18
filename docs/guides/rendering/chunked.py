from Pyjoyment.Lite import *


@get('/')
def index(c):
    c.write_chunk(b'<html><head><title>Example</title></head>', lambda c: c.finish(b'<body>Example</body></html>'))


app.start()
