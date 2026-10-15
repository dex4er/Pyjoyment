import Pyjo.IOLoop

from Pyjo.Collection import c
from Pyjo.Util import die

import sys

import dns.message
import dns.rdataclass
import dns.rdatatype


name = c(*sys.argv).get(1) or die('Usage: resolv_dns.py name [type] [nameserver]')
rtype = c(*sys.argv).get(2, 'A')
ns = c(*sys.argv).get(3, '8.8.8.8')


@Pyjo.IOLoop.timer(5)
def timeout(loop):
    print('Timeout', file=sys.stderr)
    loop.stop()


@Pyjo.IOLoop.datagram
def client(loop, datagram, id):

    @datagram.on
    def message(datagram, data, peer):
        for rr in dns.message.from_wire(data).answer:
            print(rr.to_text())
        loop.remove(timeout)
        datagram.close()

    @datagram.on
    def error(datagram, err):
        print(f'Error: {err}', file=sys.stderr)
        loop.stop()

    query = dns.message.make_query(name, dns.rdatatype.from_text(rtype), dns.rdataclass.from_text('IN'))
    datagram.send(query.to_wire(), (ns, 53))


Pyjo.IOLoop.start()
