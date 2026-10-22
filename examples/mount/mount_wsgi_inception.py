import Pyjo.Server.WSGI
import Pyjoyment

from Pyjoyment.Lite import *


# Hello world of Pyjoyment as a WSGI application, whose script name is the path it is mounted under
hello = Pyjoyment.new()
hello.routes.get('/').to(cb=lambda c: c.render(text=f'Hello Pyjoyment at {c.url_for("/")} on WSGI!'))
wsgi = Pyjo.Server.WSGI.new(app=hello).to_wsgi_app()

# The WSGI application under /wsgi of the application of Pyjoyment.Lite
plugin('Mount', {'/wsgi': wsgi})

get('/', {'text': 'I ♥ Pyjoyment!'})

# The application of a WSGI server too, which PYJO_WSGI tells: PYJO_WSGI=1 gunicorn mount_wsgi_inception:application
application = app.start()
