import Pyjo.UserAgent

from Pyjo.Util import die

import codecs
import sys


if sys.stdout.isatty():
    sys.stdout = codecs.getwriter(sys.stdout.encoding)(
        sys.stdout.detach() if hasattr(sys.stdout, 'detach') else sys.stdout, 'xmlcharrefreplace'
    )
else:
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach() if hasattr(sys.stdout, 'detach') else sys.stdout)

try:
    url = sys.argv[1]
except IndexError:
    raise Exception('get.py url opts') from None

opts = {name: int(value) if value.isdigit() else value for name, value in (a.split('=', 1) for a in sys.argv[2:])}

tx = Pyjo.UserAgent.new(**opts).get(url)
err = tx.error
if err:
    if err.get('code'):
        die('{code} response: {message}'.format(**err))
    else:
        die('Connection error: {message}'.format(**err))
print(tx.res.text)
