#!/usr/bin/env python
from Pyjoyment.Lite import *


@get('/')
def index(c):
    c.render(text='Hello World!')


app.start()
