import Pyjo.HelloWorld
import Pyjo.Server.Lambda


# The handler "hello_world_lambda.handler" of an event function of AWS Lambda
handler = Pyjo.Server.Lambda.new(app=Pyjo.HelloWorld.new()).to_lambda_app()
