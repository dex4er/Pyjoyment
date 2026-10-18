from Pyjoyment.Lite import *


app.exception_format = 'json'


@get('/json')
def json(c):
    raise Exception('Just a test')


@get('/txt')
def txt(c):
    c.exception_format('txt')
    raise Exception('Just a test')


app.start()
