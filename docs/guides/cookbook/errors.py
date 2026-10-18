import Pyjo.IOLoop

from Pyjoyment.Lite import *


# Forward error messages to the application log
Pyjo.IOLoop.singleton.reactor.on('error', lambda reactor, err: app.log.error(err))


# Exception only gets logged (and connection times out)
@get('/connection_times_out')
def connection_times_out(c):
    def fail(loop):
        raise Exception('This request will not be getting a response')

    Pyjo.IOLoop.timer(2, fail)


# Exception gets caught and handled
@get('/catch_exception')
def catch_exception(c):
    def fail(loop):
        try:
            raise Exception('This request will be getting a response')
        except Exception as err:
            c.reply.exception(err)

    Pyjo.IOLoop.timer(2, fail)


app.start()
