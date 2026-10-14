import http.client
import os
import socket
import subprocess
import time


# A server of the dependency group "servers", started in a process of its own on a free port, for the tests in
# t/servers


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class Server:
    def __init__(self, dir, command):
        # The command is a list of the program and its arguments, which name the port as {port}
        self.port = free_port()
        args = [arg.format(port=self.port) for arg in command]
        # The warnings of the servers and their libraries are not ours, so they are not errors there as in CI
        env = {k: v for k, v in os.environ.items() if k != 'PYTHONWARNINGS'} | {
            'PYTHONPATH': os.pathsep.join([dir, ROOT])
        }
        self.log = open(os.path.join(dir, 'server.log'), 'w+')
        self.process = subprocess.Popen(args, cwd=dir, env=env, stdout=self.log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                socket.create_connection(('127.0.0.1', self.port), 0.2).close()
                return
            except OSError:
                time.sleep(0.1)
        self.close()
        raise RuntimeError(f'the server did not start: {self.output()}')

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()

    def output(self):
        self.log.seek(0)
        return self.log.read()

    def request(self, method, path, body=None, headers=None, chunked=False, timeout=10):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=timeout)
        try:
            conn.request(method, path, body=body, headers=headers or {}, encode_chunked=chunked)
            res = conn.getresponse()
            return res.status, res.headers, res.read()
        finally:
            conn.close()

    def websocket(self, path):
        from websockets.sync.client import connect

        return connect(f'ws://127.0.0.1:{self.port}{path}', open_timeout=10, close_timeout=2)


if __name__ == '__main__':
    from Pyjo.Test import plan

    plan(skip_all='helper module, not a test')
