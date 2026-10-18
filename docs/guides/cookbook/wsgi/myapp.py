from Pyjoyment.Lite import *


get('/', lambda c: c.render(text=f'Hello {c.app.config("foo")}!'))

application = app.start()
