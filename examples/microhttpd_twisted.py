import sys

from twisted.internet import protocol, reactor


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


class HTTPD(protocol.Protocol):
    def dataReceived(self, chunk):
        if chunk.find(b'\x0d\x0a\x0d\x0a') >= 0:
            if chunk.find(b'\x0d\x0aConnection: Keep-Alive\x0d\x0a') >= 0:
                keepalive = True
            else:
                keepalive = False

            # Write a minimal HTTP response
            # (the "Hello World!" message has been optimized away!)
            response = b'HTTP/1.1 200 OK\x0d\x0aContent-Length: 0\x0d\x0a'
            if keepalive:
                response += b'Connection: keep-alive\x0d\x0a'
            response += b'\x0d\x0a'

            self.transport.write(response)

            if not keepalive:
                self.transport.loseConnection()


class HTTPDFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return HTTPD()


if __name__ == '__main__':
    reactor.listenTCP(port, HTTPDFactory())
    reactor.run()
