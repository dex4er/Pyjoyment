import select
import socket
import socketserver
import threading


# A SOCKS5 proxy server for the tests, as the server of IO::Socket::Socks in Mojo's tests: the CONNECT command, with
# an optional user and password of RFC 1929, in threads of its own
class SocksServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, user=None, password=None):
        super().__init__(('127.0.0.1', 0), _Handler)
        self.user = user
        self.password = password
        # The port of the last connection to a target, as $last in user_agent_socks.t
        self.last = None
        self.thread = threading.Thread(target=self.serve_forever, daemon=True)
        self.thread.start()

    @property
    def port(self):
        return self.server_address[1]

    # A client that goes away in the middle of the handshake is no error of the server
    def handle_error(self, request, client_address):
        pass

    def close(self):
        self.shutdown()
        self.server_close()


class _Handler(socketserver.BaseRequestHandler):
    def handle(self):
        client = self.request
        server = self.server

        # The auth mechanisms
        _, nmethods = _read(client, 2)
        methods = _read(client, nmethods)
        method = 0x02 if server.user is not None else 0x00
        if method not in methods:
            client.sendall(b'\x05\xff')
            return
        client.sendall(bytes([0x05, method]))

        # The user and the password
        if method == 0x02:
            _, length = _read(client, 2)
            user = _read(client, length).decode()
            (length,) = _read(client, 1)
            password = _read(client, length).decode()
            if (user, password) != (server.user, server.password):
                client.sendall(b'\x01\x01')
                return
            client.sendall(b'\x01\x00')

        # The command
        _, command, _, atyp = _read(client, 4)
        if atyp == 0x03:
            (length,) = _read(client, 1)
            host = _read(client, length).decode()
        elif atyp == 0x01:
            host = socket.inet_ntop(socket.AF_INET, _read(client, 4))
        else:
            host = socket.inet_ntop(socket.AF_INET6, _read(client, 16))
        port = int.from_bytes(_read(client, 2), 'big')
        if command != 0x01:
            client.sendall(b'\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00')
            return
        try:
            target = socket.create_connection((host, port))
        except OSError:
            client.sendall(b'\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00')
            return
        server.last = target.getsockname()[1]
        client.sendall(b'\x05\x00\x00\x01\x7f\x00\x00\x01' + server.last.to_bytes(2, 'big'))

        # The data in both directions, until one of them closes
        with target:
            sockets = [client, target]
            while True:
                readable, _, _ = select.select(sockets, [], [], 30)
                if not readable:
                    return
                for sock in readable:
                    data = sock.recv(65536)
                    if not data:
                        return
                    (target if sock is client else client).sendall(data)


def _read(sock, length):
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError('closed')
        data += chunk
    return data


def new(user=None, password=None):
    return SocksServer(user, password)


if __name__ == '__main__':
    from Pyjo.Test import plan

    plan(skip_all='helper module, not a test')
