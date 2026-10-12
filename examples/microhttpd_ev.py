import socket
import sys
import signal
import weakref
import errno
import pyev

STOPSIGNALS = (signal.SIGINT, signal.SIGTERM)
NONBLOCKING = (errno.EAGAIN, errno.EWOULDBLOCK)


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


class Connection:

    def __init__(self, sock, address, loop):
        self.sock = sock
        self.address = address
        self.sock.setblocking(0)
        self.buf = ""
        self.watcher = pyev.Io(self.sock, pyev.EV_READ, loop, self.io_cb)
        self.watcher.start()

    def reset(self, events):
        self.watcher.stop()
        self.watcher.set(self.sock, events)
        self.watcher.start()

    def handle_error(self, msg):
        print(msg)
        self.close()

    def handle_read(self):
        try:
            buf = self.sock.recv(10240)
        except OSError as err:
            if err.args[0] not in NONBLOCKING:
                self.handle_error(f"error reading from {self.sock}")
        if not buf:
            self.handle_error("connection closed by peer")
            return

        if buf.find(b"\x0d\x0a\x0d\x0a") >= 0:
            if buf.find(b"\x0d\x0aConnection: Keep-Alive\x0d\x0a") >= 0:
                self.keepalive = True
            else:
                self.keepalive = False

            # Write a minimal HTTP response
            # (the "Hello World!" message has been optimized away!)
            response = b"HTTP/1.1 200 OK\x0d\x0aContent-Length: 0\x0d\x0a"
            if self.keepalive:
                response += b"Connection: keep-alive\x0d\x0a"
            response += b"\x0d\x0a"

            self.buf = response
            self.reset(pyev.EV_READ | pyev.EV_WRITE)

    def handle_write(self):
        try:
            sent = self.sock.send(self.buf)
        except OSError as err:
            if err.args[0] not in NONBLOCKING:
                self.handle_error(f"error writing to {self.sock}")
        else:
            self.buf = self.buf[sent:]
            if not self.buf:
                self.reset(pyev.EV_READ)

        if not self.keepalive:
            self.close()

    def io_cb(self, watcher, revents):
        if revents & pyev.EV_READ:
            self.handle_read()
        else:
            self.handle_write()

    def close(self):
        self.sock.close()
        self.watcher.stop()
        self.watcher = None


class Server:

    def __init__(self, address):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(address)
        self.sock.setblocking(0)
        self.address = self.sock.getsockname()
        self.loop = pyev.default_loop()
        self.watchers = [pyev.Signal(sig, self.loop, self.signal_cb)
                         for sig in STOPSIGNALS]
        self.watchers.append(pyev.Io(self.sock, pyev.EV_READ, self.loop,
                                     self.io_cb))
        self.conns = weakref.WeakValueDictionary()

    def handle_error(self, msg):
        print(msg)
        self.stop()

    def signal_cb(self, watcher, revents):
        self.stop()

    def io_cb(self, watcher, revents):
        try:
            while True:
                try:
                    sock, address = self.sock.accept()
                except OSError as err:
                    if err.args[0] in NONBLOCKING:
                        break
                    else:
                        raise
                else:
                    self.conns[address] = Connection(sock, address, self.loop)
        except Exception:
            self.handle_error("error accepting a connection")

    def start(self):
        self.sock.listen(socket.SOMAXCONN)
        for watcher in self.watchers:
            watcher.start()
        self.loop.start()

    def stop(self):
        self.loop.stop(pyev.EVBREAK_ALL)
        self.sock.close()
        while self.watchers:
            self.watchers.pop().stop()
        for conn in self.conns.values():
            conn.close()


if __name__ == "__main__":
    server = Server(("0.0.0.0", port))
    server.start()
