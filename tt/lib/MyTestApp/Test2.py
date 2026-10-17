from Pyjoyment.Lite import get


@get('/')
def index(c):
    name = c.param('name')
    url = c.url_for()
    c.render(text=f'Bye from the {name} app! {url}!')
