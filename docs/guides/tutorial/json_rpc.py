from Pyjo.JSON.RPC import RPC, Client, Error
from Pyjoyment.Lite import *


# A method of JSON-RPC, whose parameters the schema of its type hints validates
rpc = RPC()


@rpc.method(schema=True)
def divide(a: float, b: float) -> float:
    if b == 0:
        raise Error.new(1, 'Division by zero')
    return a / b


# The server, which takes the requests in the body of a POST
post('/rpc', rpc.to_action())


# A client of the server, through the user agent of the application
@get('/divide/<a:num>/<b:num>')
async def quotient(c):
    client = Client.new(lambda request: c.ua().post_p('/rpc', json=request).then(lambda tx: tx.res.json()))
    try:
        c.render(json={'result': await client.call_p('divide', int(c.param('a')), int(c.param('b')))})
    except Error as e:
        c.render(json={'error': e.message, 'code': e.code}, status=400)


app.start()
