from Pyjoyment.Lite import *


# Load message into memory
hello = app.home.child('cache', 'hello.txt').slurp('UTF-8')


# Display message
@get('/')
def index(c):
    c.render(text=hello)


app.start()
