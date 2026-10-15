import Pyjo.UserAgent

from Pyjo.Util import die

import sys


# A terminal gets the characters it cannot show as HTML character references, anything else UTF-8
if sys.stdout.isatty():
    sys.stdout.reconfigure(errors='xmlcharrefreplace')
else:
    sys.stdout.reconfigure(encoding='utf-8')

url = sys.argv[1] if len(sys.argv) > 1 else die('get.py url opts')

opts = {name: int(value) if value.isdigit() else value for name, value in (a.split('=', 1) for a in sys.argv[2:])}

tx = Pyjo.UserAgent.new(**opts).get(url)
if err := tx.error:
    if 'code' in err:
        die(f'{err["code"]} response: {err["message"]}')
    die(f'Connection error: {err["message"]}')
print(tx.res.text)
