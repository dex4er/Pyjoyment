from wsgiref.simple_server import make_server


def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [f'Hello WSGI at {environ["SCRIPT_NAME"]} for {environ["PATH_INFO"]}!'.encode()]


if __name__ == '__main__':
    make_server('', 3000, app).serve_forever()
