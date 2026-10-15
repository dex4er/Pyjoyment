import Pyjo.HelloWorld
import Pyjo.Server.WSGI


app = Pyjo.Server.WSGI.new(app=Pyjo.HelloWorld.new()).to_wsgi_app()
