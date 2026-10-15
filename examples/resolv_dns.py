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


# DNS over TCP, where a message has its length in front of it
@Pyjo.IOLoop.client(address=ns, port=53)
def client(loop, err, stream):
    if err:
        print(f'Connection error: {err}', file=sys.stderr)
        return

    buffer = bytearray()

    @stream.on
    def read(stream, chunk):
        buffer.extend(chunk)
        if len(buffer) >= 2 and len(buffer) >= 2 + int.from_bytes(buffer[:2]):
            for rr in dns.message.from_wire(bytes(buffer[2:])).answer:
                print(rr.to_text())
            stream.close()

    query = dns.message.make_query(name, dns.rdatatype.from_text(rtype), dns.rdataclass.from_text('IN')).to_wire()
    stream.write(len(query).to_bytes(2) + query)


Pyjo.IOLoop.start()
