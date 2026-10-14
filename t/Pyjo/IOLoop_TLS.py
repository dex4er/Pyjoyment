import Pyjo.IOLoop
import Pyjo.IOLoop.TLS
import Pyjo.Promise

from Pyjo.Test import *

import os
import ssl


# Left out from Mojolicious: plan skip_all unless TEST_TLS, as the ssl module comes with Python, and unless can_tls

# Left out from Mojolicious: the commands that regenerate the certificates, which AGENTS.md has for t/certs
certs = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certs')


def cert(name):
    return os.path.join(certs, name)


# Unlike Mojolicious: tls_options of IO::Socket::SSL are contexts of the ssl module
def unverified(cert=None, key=None, alpn=None):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    if cert:
        context.load_cert_chain(cert, key)
    if alpn:
        context.set_alpn_protocols(alpn)
    return context


def server_context(cert=None, key=None, ca=None, verify=ssl.CERT_NONE, alpn=None, names=None):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert or Pyjo.IOLoop.TLS.CERT, key or Pyjo.IOLoop.TLS.KEY)
    if ca:
        context.load_verify_locations(ca)
    context.verify_mode = verify
    if alpn:
        context.set_alpn_protocols(alpn)
    if names is not None:
        context.sni_callback = lambda socket, name, context: names.append(name)
    return context


# Built-in certificate (and upgraded string)
loop = Pyjo.IOLoop.new()
# Left out from Mojolicious: utf8::upgrade, as the chunk is bytes
upgraded = b'\x01\x00\x00\x00\x00\x00\xd0\x00\x0a\x00\x0b\x00\x00\x00\x84\x0b'
server = client = b''
promise = Pyjo.Promise.new().set(ioloop=loop)


def server_cb(loop, stream, id):
    def read(stream, chunk):
        global server
        server += chunk

    stream.write(upgraded, lambda stream: stream.write(b'321'))
    stream.on('close', lambda stream: promise.resolve())
    stream.on('read', read)


id = loop.server(server_cb, address='127.0.0.1', tls=True)
port = loop.acceptor(id).port
promise2 = Pyjo.Promise.new().set(ioloop=loop)


def client_cb(loop, err, stream):
    def read(stream, chunk):
        global client
        client += chunk

    stream.write(b'tset', lambda stream: stream.write(b'123'))
    stream.on('close', lambda stream: promise2.resolve())
    stream.on('read', read)
    stream.timeout = 0.5


loop.client(client_cb, port=port, tls=True, tls_context=unverified())
Pyjo.Promise.all(promise, promise2).wait()
is_ok(server, b'tset123', 'right content')
is_ok(client, upgraded + b'321', 'right content')

# Valid client certificate
server = client = b''
remove = running = timeout = server_err = server_close = client_close = None


def remove_cb(loop):
    global remove
    remove = True


Pyjo.IOLoop.remove(Pyjo.IOLoop.recurring(0, remove_cb))
promise = Pyjo.Promise.new()


def valid_server_cb(loop, stream, id):
    global running

    def timeout_cb(stream):
        global timeout
        timeout = (timeout or 0) + 1

    def close_cb(stream):
        global server_close
        server_close = (server_close or 0) + 1
        promise.resolve()

    def error_cb(stream, err):
        global server_err
        server_err = err

    def read(stream, chunk):
        global server
        server += chunk

    stream.write(b'test', lambda stream: stream.write(b'321'))
    running = Pyjo.IOLoop.is_running()
    stream.on('timeout', timeout_cb)
    stream.on('close', close_cb)
    stream.on('error', error_cb)
    stream.on('read', read)
    stream.timeout = 0.5


id = Pyjo.IOLoop.server(
    valid_server_cb,
    address='127.0.0.1',
    tls=True,
    tls_ca=cert('ca.crt'),
    tls_cert=cert('server.crt'),
    tls_key=cert('server.key'),
)
port = Pyjo.IOLoop.acceptor(id).port
promise2 = Pyjo.Promise.new()


def valid_client_cb(loop, err, stream):
    def close_cb(stream):
        global client_close
        client_close = (client_close or 0) + 1
        promise2.resolve()

    def read(stream, chunk):
        global client
        client += chunk

    stream.write(b'tset', lambda stream: stream.write(b'123'))
    stream.on('close', close_cb)
    stream.on('read', read)


Pyjo.IOLoop.client(valid_client_cb, port=port, tls=True, tls_context=unverified(cert('client.crt'), cert('client.key')))
Pyjo.Promise.all(promise, promise2).wait()
is_ok(server, b'tset123', 'right content')
is_ok(client, b'test321', 'right content')
is_ok(timeout, 1, 'server emitted timeout event once')
is_ok(server_close, 1, 'server emitted close event once')
is_ok(client_close, 1, 'client emitted close event once')
ok(running, 'loop was running')
ok(not remove, 'event removed successfully')
ok(not server_err, 'no error')

# Invalid client certificate
client_err = None


def error_client_cb(loop, err, stream):
    global client_err
    loop.stop()
    client_err = err


Pyjo.IOLoop.client(error_client_cb, port=port, tls=True, tls_cert=cert('bad.crt'), tls_key=cert('bad.key'))
Pyjo.IOLoop.start()
ok(client_err, 'has error')

# Missing client certificate
server_err = client_err = None
Pyjo.IOLoop.client(error_client_cb, port=port, tls=True)
Pyjo.IOLoop.start()
ok(not server_err, 'no error')
ok(client_err, 'has error')


def accepted_cb(loop, stream, id):
    global server_err
    server_err = 'accepted'


# Invalid certificate authority (server)
loop = Pyjo.IOLoop.new()
server_err = client_err = None
id = loop.server(
    accepted_cb,
    address='127.0.0.1',
    tls=True,
    tls_ca='no cert',
    tls_cert=cert('server.crt'),
    tls_key=cert('server.key'),
)
port = loop.acceptor(id).port
loop.client(error_client_cb, port=port, tls=True, tls_cert=cert('client.crt'), tls_key=cert('client.key'))
loop.start()
ok(not server_err, 'no error')
ok(client_err, 'has error')

# Valid client and server certificates
running = timeout = server_err = server_close = None
server = client = b''
client_close = None
promise = Pyjo.Promise.new()


def valid2_server_cb(loop, stream, id):
    global running

    def close_cb(stream):
        global server_close
        server_close = (server_close or 0) + 1
        promise.resolve()

    def error_cb(stream, err):
        global server_err
        server_err = err

    def read(stream, chunk):
        global server
        server += chunk

    stream.write(b'test', lambda stream: stream.write(b'321'))
    running = Pyjo.IOLoop.is_running()
    stream.on('close', close_cb)
    stream.on('error', error_cb)
    stream.on('read', read)


id = Pyjo.IOLoop.server(
    valid2_server_cb,
    address='127.0.0.1',
    tls=True,
    tls_ca=cert('ca.crt'),
    tls_cert=cert('server.crt'),
    tls_key=cert('server.key'),
)
port = Pyjo.IOLoop.acceptor(id).port
promise2 = Pyjo.Promise.new()


def valid2_client_cb(loop, err, stream):
    def timeout_cb(stream):
        global timeout
        timeout = (timeout or 0) + 1

    def close_cb(stream):
        global client_close
        client_close = (client_close or 0) + 1
        promise2.resolve()

    def read(stream, chunk):
        global client
        client += chunk

    stream.write(b'tset', lambda stream: stream.write(b'123'))
    stream.on('timeout', timeout_cb)
    stream.on('close', close_cb)
    stream.on('read', read)
    stream.timeout = 0.5


Pyjo.IOLoop.client(
    valid2_client_cb,
    port=port,
    tls=True,
    tls_ca=cert('ca.crt'),
    tls_cert=cert('client.crt'),
    tls_key=cert('client.key'),
)
Pyjo.Promise.all(promise, promise2).wait()
is_ok(server, b'tset123', 'right content')
is_ok(client, b'test321', 'right content')
is_ok(timeout, 1, 'server emitted timeout event once')
is_ok(server_close, 1, 'server emitted close event once')
is_ok(client_close, 1, 'client emitted close event once')
ok(running, 'loop was running')
ok(not server_err, 'no error')

# Invalid server certificate (unsigned)
loop = Pyjo.IOLoop.new()
server_err = client_err = None
id = loop.server(accepted_cb, address='127.0.0.1', tls=True, tls_cert=cert('bad.crt'), tls_key=cert('bad.key'))
port = loop.acceptor(id).port
loop.client(error_client_cb, port=port, tls=True, tls_ca=cert('ca.crt'))
loop.start()
ok(not server_err, 'no error')
ok(client_err, 'has error')

# Invalid server certificate (hostname)
loop = Pyjo.IOLoop.new()
server_err = client_err = None
id = loop.server(accepted_cb, address='127.0.0.1', tls=True, tls_cert=cert('bad.crt'), tls_key=cert('bad.key'))
port = loop.acceptor(id).port
loop.client(error_client_cb, address='127.0.0.1', port=port, tls=True, tls_ca=cert('ca.crt'))
loop.start()
ok(not server_err, 'no error')
ok(client_err, 'has error')

# Invalid certificate authority (client)
loop = Pyjo.IOLoop.new()
server_err = client_err = None
id = loop.server(accepted_cb, address='127.0.0.1', tls=True, tls_cert=cert('bad.crt'), tls_key=cert('bad.key'))
port = loop.acceptor(id).port
loop.client(error_client_cb, port=port, tls=True, tls_ca='no cert')
loop.start()
ok(not server_err, 'no error')
ok(client_err, 'has error')

# Ignore invalid client certificate
loop = Pyjo.IOLoop.new()
cipher = version = None
server = client = client_err = None


def ignore_server_cb(loop, stream, id):
    global server
    stream.on('close', lambda stream: loop.stop())
    server = 'accepted'


context = server_context(cert('server.crt'), cert('server.key'), cert('ca.crt'))
context.set_ciphers('AES256-SHA:ALL')
id = loop.server(ignore_server_cb, address='127.0.0.1', tls=True, tls_context=context)
port = loop.acceptor(id).port


def ignore_client_cb(loop, err, stream):
    global client_err, client, cipher, version
    stream.timeout = 0.5
    client_err = err
    client = 'connected'
    handle = stream.handle
    cipher = handle.cipher()[0]
    version = handle.version()


loop.client(ignore_client_cb, port=port, tls=True, tls_context=unverified(cert('bad.crt'), cert('bad.key')))
loop.start()
is_ok(server, 'accepted', 'right result')
is_ok(client, 'connected', 'right result')
ok(not client_err, 'no error')
expect = 'TLS_AES_256_GCM_SHA384' if version == 'TLSv1.3' else 'AES256-SHA'
is_ok(cipher, expect, f'{expect} has been negotiated')

# Ignore missing client certificate
server = client = client_err = None


def missing_server_cb(loop, stream, id):
    global server
    server = 'accepted'


def missing_client_cb(loop, err, stream):
    global client, client_err
    loop.stop()
    client = 'connected'
    client_err = err


# SSL_verify_mode => 0x01 and SSL_version => 'TLSv1_2'
context = server_context(cert('server.crt'), cert('server.key'), cert('ca.crt'), ssl.CERT_OPTIONAL)
context.minimum_version = context.maximum_version = ssl.TLSVersion.TLSv1_2
id = Pyjo.IOLoop.server(missing_server_cb, address='127.0.0.1', tls=True, tls_context=context)
port = Pyjo.IOLoop.acceptor(id).port
Pyjo.IOLoop.client(missing_client_cb, port=port, tls=True, tls_context=unverified())
Pyjo.IOLoop.start()
is_ok(server, 'accepted', 'right result')
is_ok(client, 'connected', 'right result')
ok(not client_err, 'no error')

with subtest('ALPN'):
    server_proto = client_proto = None

    def alpn_server_cb(loop, stream, id):
        global server_proto
        server_proto = stream.handle.selected_alpn_protocol()
        stream.close()

    id = Pyjo.IOLoop.server(
        alpn_server_cb, address='127.0.0.1', tls=True, tls_context=server_context(alpn=['foo', 'bar', 'baz'])
    )
    port = Pyjo.IOLoop.acceptor(id).port

    def alpn_client_cb(loop, err, stream):
        global client_proto
        client_proto = stream.handle.selected_alpn_protocol()
        stream.on('close', lambda stream: Pyjo.IOLoop.stop())

    Pyjo.IOLoop.client(alpn_client_cb, port=port, tls=True, tls_context=unverified(alpn=['baz', 'bar']))
    Pyjo.IOLoop.start()
    # Unlike Mojolicious: OpenSSL chooses by the order of the server, IO::Socket::SSL by the order of the client
    is_ok(server_proto, 'bar', 'right protocol')
    is_ok(client_proto, 'bar', 'right protocol')


def sni_server(names):
    def cb(loop, stream, id):
        stream.close()

    return cb


def sni_client_cb(loop, err, stream):
    stream.on('close', lambda stream: Pyjo.IOLoop.stop())


with subtest('conditionally override SSL_hostname'):
    # Unlike Mojolicious: the server of Python sees the name of SNI in the callback of its context
    names = []
    id = Pyjo.IOLoop.server(sni_server(names), address='127.0.0.1', tls=True, tls_context=server_context(names=names))
    port = Pyjo.IOLoop.acceptor(id).port
    # Not in Mojolicious: tls_hostname for SSL_hostname
    Pyjo.IOLoop.client(sni_client_cb, port=port, tls=True, tls_hostname='mojolicious.org', tls_context=unverified())
    Pyjo.IOLoop.start()
    sni = names[0] if names else None
    is_ok(sni, 'mojolicious.org', 'right sni')

with subtest('can disable SNI'):
    names = []
    id = Pyjo.IOLoop.server(sni_server(names), address='127.0.0.1', tls=True, tls_context=server_context(names=names))
    port = Pyjo.IOLoop.acceptor(id).port
    Pyjo.IOLoop.client(sni_client_cb, port=port, tls=True, tls_hostname='', tls_context=unverified())
    Pyjo.IOLoop.start()
    sni = names[0] if names else None
    ok(not sni, 'sni disabled')

with subtest('SNI defaults to address'):
    names = []
    id = Pyjo.IOLoop.server(sni_server(names), address='localhost', tls=True, tls_context=server_context(names=names))
    port = Pyjo.IOLoop.acceptor(id).port
    Pyjo.IOLoop.client(sni_client_cb, address='localhost', port=port, tls=True, tls_context=unverified())
    Pyjo.IOLoop.start()
    sni = names[0] if names else None
    is_ok(sni, 'localhost', 'sni defaults to address')

with subtest('valid certificates with custom verifycn_name'):
    client_err = server_err = running = None
    promise = Pyjo.Promise.new()

    def verifycn_server_cb(loop, stream, id):
        global running

        def error_cb(stream, err):
            global server_err
            server_err = err

        running = Pyjo.IOLoop.is_running()
        stream.on('close', lambda stream: promise.resolve())
        stream.on('error', error_cb)

    id = Pyjo.IOLoop.server(
        verifycn_server_cb,
        address='127.0.0.1',
        tls=True,
        tls_ca=cert('ca.crt'),
        tls_cert=cert('mojo_server.crt'),
        tls_key=cert('mojo_server.key'),
    )
    port = Pyjo.IOLoop.acceptor(id).port
    promise2 = Pyjo.Promise.new()

    def verifycn_client_cb(loop, err, stream):
        def error_cb(stream, err):
            global client_err
            client_err = err

        stream.on('close', lambda stream: promise2.resolve())
        stream.on('error', error_cb)
        stream.close()

    # Not in Mojolicious: tls_hostname for SSL_verifycn_name, which is the name for SNI too
    Pyjo.IOLoop.client(
        verifycn_client_cb,
        port=port,
        tls=True,
        tls_ca=cert('ca.crt'),
        tls_cert=cert('client.crt'),
        tls_key=cert('client.key'),
        tls_hostname='mojolicious.org',
    )
    Pyjo.Promise.all(promise, promise2).wait()
    ok(running, 'loop was running')
    ok(not server_err, 'no server error')
    ok(not client_err, 'no client error')

done_testing()
