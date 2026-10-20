from Pyjoyment.Lite import app, get


@get('/')
def index(c):
    c.render(text='Hello')


app.start()
