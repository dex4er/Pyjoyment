#!/usr/bin/env python
from Pyjoyment.Lite import *

from MyApp.Model.Users import Users


# Helper to store our model object
users = Users()
helper('users', lambda c: users)


# /?user=sebastian&pass=secr3t
@any('/')
def index(c):

    # Query parameters
    user = c.param('user') or ''
    password = c.param('pass') or ''

    # Check password
    if c.users().check(user, password):
        return c.render(text=f'Welcome {user}.')

    # Failed
    c.render(text='Wrong username or password.')


app.start()
