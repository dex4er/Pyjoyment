from Pyjoyment.Lite import *


@get('/')
def index(c):
    c.reply.static('index.html')


@get('/some_download')
def some_download(c):
    c.res.headers.content_disposition = 'attachment; filename=bar.png;'
    c.reply.static('foo/bar.png')


@get('/leak')
def leak(c):
    c.reply.file('/etc/passwd')


app.start()
