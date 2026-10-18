from Pyjoyment.Lite import *


# Not found (404)
@get('/missing')
def missing(c):
    c.reply.not_found()


# Exception (500)
@get('/dies')
def dies(c):
    raise Exception('Intentional error')


app.start()
