import Pyjo.HelloWorld
import Pyjo.Server.ASGI

import uvicorn


app = Pyjo.Server.ASGI.new(app=Pyjo.HelloWorld.new()).to_asgi_app()

uvicorn.run(app, port=3000)
