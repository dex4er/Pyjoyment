from Pyjo.Util import secure_compare
from Pyjoyment.Lite import *


@get('/')
def index(c):
    # Check for username "Bender" and password "rocks"
    if secure_compare(c.req.url.to_abs().userinfo or '', 'Bender:rocks'):
        return c.render(text='Hello Bender!')

    # Require authentication
    c.res.headers.www_authenticate = 'Basic'
    c.render(text='Authentication required!', status=401)


app.start()
