import Pyjo.Server.WSGI
import Pyjoyment.HelloWorld


app = Pyjo.Server.WSGI.new(app=Pyjoyment.HelloWorld.new()).to_wsgi_app()
