from Pyjoyment.Lite import *

import re


# Firefox
@get('/foo').requires(agent=re.compile(r'Firefox'))
def firefox(c):
    c.render(text='Congratulations, you are using a cool browser.')


# Internet Explorer
@get('/foo').requires(agent=re.compile(r'Internet Explorer'))
def internet_explorer(c):
    c.render(text='Dude, you really need to upgrade to Firefox.')


# http://mojolicious.org/bar
@get('/bar').requires(host='mojolicious.org')
def bar(c):
    c.render(text='Hello Mojolicious.')


app.start()
