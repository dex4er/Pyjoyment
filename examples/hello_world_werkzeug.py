import Pyjo.HelloWorld
import Pyjo.Server.WSGI

from werkzeug.serving import run_simple


app = Pyjo.Server.WSGI.new(app=Pyjo.HelloWorld.new()).to_wsgi_app()

run_simple('localhost', 3000, app)
