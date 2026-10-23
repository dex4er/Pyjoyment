from Pyjoyment.Lite import *


# The hosts of the deployment, and of localhost for development, and the origin of its pages
plugin('AllowedHosts', hosts=['example.com', '.example.com', 'localhost', '127.0.0.1'], origins=['https://example.com'])


@get('/')
def index(c):
    c.render(text='Hello World!')


app.start()
