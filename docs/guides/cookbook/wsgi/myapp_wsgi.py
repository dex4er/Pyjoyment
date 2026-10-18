import Pyjo.Server.WSGI


# A WSGI middleware, as the ones of Werkzeug or WhiteNoise
def powered_by(application):
    def middleware(environ, start_response):
        def start(status, headers, exc_info=None):
            return start_response(status, [*headers, ('X-Powered-By', 'Pyjoyment')], exc_info)

        return application(environ, start)

    return middleware


server = Pyjo.Server.WSGI.new()
server.load_app('./myapp.py')
server.app.config(foo='bar')
application = powered_by(server.to_wsgi_app())
