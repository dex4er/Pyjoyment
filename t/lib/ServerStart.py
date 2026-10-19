import fcntl
import os
import random
import socket
import tempfile
import time


# A server that a test starts in a process of its own listens on a port that the test gives it, which the test finds
# free, but until the process binds it, which takes the start of an interpreter, another process can take it: a server
# that listens on a port that the system picks, as many tests start, or an outgoing connection, whose local port the
# system picks too. The system picks them from its ephemeral ports, which start at 32768 on Linux and 49152 on macOS,
# so the port is found below them, and a lock of the byte of the port in a file of the temporary directory, which the
# system releases when the process of the test ends, keeps it from the other tests. A server that cannot bind its port
# anyway, as one of another program, is started again on a new port, and the test waits for it with a limit of time, so
# that a server that does not start fails the test instead of hanging it until the timeout of Pyjo.Prove


# The ports below the ephemeral ones of the systems
PORTS = range(20000, 30000)

# The locks of a process are released when it closes any descriptor of the file, so it keeps one
_locks = None

ATTEMPTS = 3


def port():
    # A port that is free now, which no socket of the system takes by itself, and no other test
    global _locks
    if _locks is None:
        _locks = os.open(
            os.path.join(tempfile.gettempdir(), 'pyjoyment-test-ports.lock'), os.O_RDWR | os.O_CREAT, 0o666
        )
    while True:
        port = random.choice(PORTS)
        try:
            fcntl.lockf(_locks, fcntl.LOCK_EX | fcntl.LOCK_NB, 1, port)
        except OSError:
            continue
        try:
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', port))
        except OSError:
            continue
        return port


def retry(start):
    # start generates the ports, starts the server and returns what the test needs, or None when the server did not
    # listen on its ports
    for _ in range(ATTEMPTS):
        if (started := start()) is not None:
            return started
    raise RuntimeError(f'the server did not start in {ATTEMPTS} attempts')


def in_use(result):
    # The result of subprocess.run of a server that could not bind a port, with its standard error captured
    return result.returncode != 0 and 'Address already in use' in (result.stderr or '')


def listening(port, process=None, timeout=20):
    # The port accepts connections, False when the process of the server has ended before, and an error when the time
    # is up
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            socket.create_connection(('127.0.0.1', port), 0.2).close()
            return True
        except OSError:
            if process is not None and process.poll() is not None:
                return False
            time.sleep(0.1)
    raise TimeoutError(f'port {port} does not accept connections after {timeout} seconds')


def wait_for(condition, what, timeout=30, interval=0.1):
    deadline = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > deadline:
            raise TimeoutError(f'waited {timeout} seconds for {what}')
        time.sleep(interval)


if __name__ == '__main__':
    from Pyjo.Test import plan

    plan(skip_all='helper module, not a test')
