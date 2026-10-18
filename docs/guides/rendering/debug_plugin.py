from Pyjoyment.Lite import *


plugin('DebugHelper')


@get('/')
def index(c):
    c.debug('It works!')
    c.render(text='Hello!')


app.start()
