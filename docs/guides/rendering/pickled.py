from Pyjoyment.Lite import *

import pickle


# Add "pickle" handler
def pickle_handler(renderer, c, output, options):

    # Disable automatic encoding
    options.pop('encoding', None)

    # Encode data from stash value
    output.write(pickle.dumps(c.stash().pop('pickle')))


app.renderer.add_handler('pickle', pickle_handler)


# Set "handler" value automatically if "pickle" value is set already
@hook('before_render')
def before_render(c, args):
    if 'pickle' in args or 'pickle' in c.stash():
        args['handler'] = 'pickle'


get('/', {'pickle': {'i': '♥ pyjoyment'}})

app.start()
