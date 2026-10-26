from Pyjoyment.Lite import *

import os


# The directory of the uploads, which the application writes to, so it is not ready without it
UPLOADS = os.environ.get('MYAPP_UPLOADS', '/var/lib/myapp/uploads')

plugin('Health', checks={'uploads': lambda c: os.access(UPLOADS, os.W_OK)})


@get('/')
def index(c):
    c.render(text='Hello World!')


app.start()
