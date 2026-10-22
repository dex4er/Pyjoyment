from Pyjoyment.Lite import *


@get('/')
def index(c):
    c.render(text=f'Hello Lambda at {c.url_for("/")}!')


# The handler "myapp.handler" of an event function of AWS Lambda, and the command of the arguments otherwise
handler = app.start()
