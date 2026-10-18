import Pyjo.Promise
import Pyjo.URL

from Pyjoyment.Lite import *


# Search GitHub for "pyjoyment" and "mojolicious"
@get('/')
def index(c):
    # Create two promises
    url = Pyjo.URL.new('https://api.github.com/search/repositories')
    pyjo = c.ua().get_p(url.clone().set(query={'q': 'pyjoyment'}))
    mojo = c.ua().get_p(url.clone().set(query={'q': 'mojolicious'}))

    # Render a response once both promises have been resolved
    @Pyjo.Promise.all(pyjo, mojo).then
    def render(pyjo, mojo):
        c.render(
            json={
                'pyjo': pyjo[0].result.json('/items/0/full_name'),
                'mojo': mojo[0].result.json('/items/0/full_name'),
            }
        )

    render.catch(lambda err: c.reply.exception(err)).wait()


app.start()
