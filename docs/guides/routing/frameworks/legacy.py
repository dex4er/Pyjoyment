# A WSGI application, as an application of Flask is one
def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [f'Hello from WSGI at {environ["SCRIPT_NAME"]} for {environ["PATH_INFO"]}!'.encode()]
