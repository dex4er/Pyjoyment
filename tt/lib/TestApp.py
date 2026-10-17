from Pyjoyment.Lite import app, get


__all__ = ['app']


@get('/hello')
def hello(c):
    name = c.stash('name')
    session = c.session()
    session['counter'] = counter = session.get('counter', 0) + 1
    c.render(text=f'Hello from the {name} ({counter}) app!')
