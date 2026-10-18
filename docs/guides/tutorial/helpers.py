"""
__DATA__

@@ secret.html.ep
We know who you are <%= whois() %>.
"""

from Pyjoyment.Lite import *


# A helper to identify visitors
@helper('whois')
def whois(c):
    agent = c.req.headers.user_agent or 'Anonymous'
    ip = c.tx.remote_address
    return f'{agent} ({ip})'


# Use helper in action and template
@get('/secret')
def secret(c):
    user = c.whois()
    c.app.log.debug(f'Request from {user}')


app.start()
