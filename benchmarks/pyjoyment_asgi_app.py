import Pyjo.Server.ASGI
import Pyjoyment.HelloWorld


app = Pyjo.Server.ASGI.new(app=Pyjoyment.HelloWorld.new()).to_asgi_app()
