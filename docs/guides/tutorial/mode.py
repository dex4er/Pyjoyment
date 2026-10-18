from Pyjoyment.Lite import *


# Prepare mode specific message during startup
msg = 'Development!' if app.mode == 'development' else 'Something else!'


@get('/')
def index(c):
    c.app.log.debug('Rendering mode specific message')
    c.render(text=msg)


app.log.debug('Starting application')
app.start()
