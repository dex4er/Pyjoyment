import Pyjo.UserAgent
from Pyjo.String.Unicode import u

tx = Pyjo.UserAgent.new().get('https://html.spec.whatwg.org')
for n in tx.res.dom('#named-character-references-table tbody > tr').each():
    name = u(n.at('td > code').text).trim()
    char = ''
    for c in u(n.children('td')[1].text).trim().split(' '):
        c = int(c.replace('U+', ''), 16)
        if c < 0x80:
            c = f'"\\x{c:02x}"'
        elif c < 0x100:
            c = f'u"\\x{c:02x}"'
        elif c < 0x10000:
            c = f'u"\\u{c:04x}"'
        else:
            c = f'u"\\U{c:08x}"'
        char += c
    u(f'    "{name}": {char},').say()
