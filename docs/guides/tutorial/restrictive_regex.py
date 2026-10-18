from Pyjoyment.Lite import *

import re


# /1
# /123
@any('/:bar', bar=re.compile(r'\d+'))
def bar(c):
    bar = c.param('bar')
    c.render(text=f'Our :bar placeholder matched {bar}')


app.start()
