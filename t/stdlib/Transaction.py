import Pyjo.Transaction.HTTP

from Pyjo.Test import *
from Pyjo.Util import network_contains

import ipaddress


with subtest('network_contains and ipaddress'):
    cases = [
        ('10.0.0.0/8', '10.10.10.10'),
        ('10.0.0.0/29', '10.10.10.10'),
        ('192.168.0.0/24', '192.168.0.1'),
        ('fc00::/7', 'fc00::c0:ff:ee'),
        ('fc00::/7', '::1'),
        ('::ffff:0:0/96', '::ffff:10.10.10.10'),
    ]
    for network, address in cases:
        is_ok(
            network_contains(network, address),
            ipaddress.ip_address(address) in ipaddress.ip_network(network),
            f'{address} in {network}',
        )

with subtest('Trusted proxies of ipaddress'):
    tx = Pyjo.Transaction.HTTP.new(original_remote_address='10.0.0.1')
    tx.req.reverse_proxy = True
    tx.req.headers.header('X-Forwarded-For', '203.0.113.7, 10.0.0.2')
    tx.req.trusted_proxies = [str(network) for network in (ipaddress.ip_network('10.0.0.0/8'),)]
    is_ok(tx.remote_address, '203.0.113.7', 'first untrusted address')
    isa_ok(ipaddress.ip_address(tx.remote_address), ipaddress.IPv4Address, 'an address for ipaddress')

done_testing()
