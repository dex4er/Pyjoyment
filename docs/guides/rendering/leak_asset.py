import Pyjo.Asset.File

from Pyjoyment.Lite import *


@get('/leak')
def leak(c):
    c.res.headers.content_type = 'text/plain'
    c.reply.asset(Pyjo.Asset.File.new(path='/etc/passwd'))


app.start()
