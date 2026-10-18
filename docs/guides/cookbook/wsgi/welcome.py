from Pyjoyment.Lite import *


# A WSGI middleware, as the ones of Werkzeug or WhiteNoise
def powered_by(application):
    def middleware(environ, start_response):
        def start(status, headers, exc_info=None):
            return start_response(status, [*headers, ('X-Powered-By', 'Pyjoyment')], exc_info)

        return application(environ, start)

    return middleware


@get('/welcome')
def welcome(c):
    c.render(text='Hello Pyjo!')


application = powered_by(app.start('wsgi'))
