from Pyjoyment.Lite import *


# Render template "templates/foo/bar.html.ep"
@any('/external')
def external(c):
    c.render(template='foo/bar')


app.start()
