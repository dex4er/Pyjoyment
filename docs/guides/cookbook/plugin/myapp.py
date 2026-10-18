from Pyjoyment.Lite import *


plugin('MyApp.Plugin.MyHelpers')


@get('/')
def index(c):
    c.my_helpers.render_with_header(text='I ♥ Pyjoyment!')


app.start()
