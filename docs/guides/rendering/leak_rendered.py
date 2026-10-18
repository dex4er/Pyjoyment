import Pyjo.Asset.File

from Pyjoyment.Lite import *


@get('/leak')
def leak(c):
    c.res.headers.content_type = 'text/plain'
    c.res.content.asset = Pyjo.Asset.File.new(path='/etc/passwd')
    c.rendered(200)


app.start()
