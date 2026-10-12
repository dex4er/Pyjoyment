import Pyjo.IOLoop

from Pyjo.Collection import c
from Pyjo.Util import die

import sys

import dns.message
import dns.rdataclass
import dns.rdatatype


name = c(sys.argv).get(1) or die('Usage: dns.py name A 8.8.8.8')
rtype = c(sys.argv).get(2, 'A')
ns = c(sys.argv).get(3, '8.8.8.8')


@Pyjo.IOLoop.client(address=ns, port=53, proto='udp')
def client(loop, err, stream):

    @stream.on
    def read(stream, chunk):
        for rr in dns.message.from_wire(chunk).answer:
            print(rr.to_text())
        stream.close()

    stream.write(dns.message.make_query(name, dns.rdatatype.from_text(rtype), dns.rdataclass.from_text('IN')).to_wire())


Pyjo.IOLoop.start()
