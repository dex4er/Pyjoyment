from mangum import Mangum
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route


async def hello(request):
    return PlainTextResponse(f'Hello Starlette for {request.url.path} on Mangum!')


app = Starlette(routes=[Route('/{path:path}', hello)])

# The handler "hello_mangum.handler" of an event function of AWS Lambda, with the path that it is mounted under, the
# stage, as the base path, which Mangum leaves out
handler = Mangum(app, lifespan='off', api_gateway_base_path='/mangum')
