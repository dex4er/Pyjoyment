import Pyjo.UserAgent

import sys, codecs

if sys.stdout.isatty():
    sys.stdout = codecs.getwriter(sys.stdout.encoding)(sys.stdout, 'xmlcharrefreplace')
else:
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

try:
    url = sys.argv[1]
except IndexError:
    raise Exception('get.py url opts')

opts = dict(map(lambda a: a.split('='), sys.argv[2:]))

tx = Pyjo.UserAgent.new(**opts).get(url)
print(tx.res.text)
