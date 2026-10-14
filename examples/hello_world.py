import Pyjo.HelloWorld
import Pyjo.Server.Daemon


Pyjo.Server.Daemon.new(app=Pyjo.HelloWorld.new(), listen=['http://*:3000']).run()
