import Pyjo.HelloWorld
import Pyjo.Server.ASGI


app = Pyjo.Server.ASGI.new(app=Pyjo.HelloWorld.new()).to_asgi_app()
