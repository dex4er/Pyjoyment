import Pyjo.Server.ASGI
import Pyjoyment

from Pyjoyment.Lite import *


# Hello world of Pyjoyment as an ASGI application, whose root path is the path it is mounted under
hello = Pyjoyment.new()
hello.routes.get('/').to(cb=lambda c: c.render(text=f'Hello Pyjoyment at {c.url_for("/")} on ASGI!'))
asgi = Pyjo.Server.ASGI.new(app=hello).to_asgi_app()

# The ASGI application under /asgi of the application of Pyjoyment.Lite
plugin('Mount', {'/asgi': asgi})

get('/', {'text': 'I ♥ Pyjoyment!'})

# The application of an ASGI server too, which PYJO_ASGI tells: PYJO_ASGI=1 uvicorn mount_asgi_inception:application
application = app.start()
