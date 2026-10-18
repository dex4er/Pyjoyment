from Pyjoyment.Lite import *


# /hello
# /hello.json
# /hello.txt
@get('/hello', {'format': 'txt'}, format=['json', 'txt'])
def hello(c):
    if c.stash('format') == 'json':
        return c.render(json={'hello': 'world'})
    c.render(text='hello world')


app.start()
