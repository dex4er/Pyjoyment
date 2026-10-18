from Pyjoyment.Lite import *


@hook('before_render')
def before_render(c, args):

    # Make sure we are rendering the exception template
    if (template := args.get('template')) is None:
        return
    if template != 'exception':
        return

    # Switch to JSON rendering if content negotiation allows it
    if not c.accepts('json'):
        return
    args['json'] = {'exception': str(c.stash('exception'))}


@get('/')
def index(c):
    raise Exception('This should not happen!')


app.start()
