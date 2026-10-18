"""
__DATA__

@@ denied.html.ep
You are not Bender, permission denied.

@@ index.html.ep
Hi Bender.
"""

from Pyjoyment.Lite import *


# Authenticate based on name parameter
@under
def authenticate(c):

    # Authenticated
    name = c.param('name') or ''
    if name == 'Bender':
        return True

    # Not authenticated
    c.render(template='denied')
    return None


# Only reached when authenticated
get('/', 'index')

app.start()
