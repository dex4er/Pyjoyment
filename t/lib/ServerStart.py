import socket
import time


# A server that a test starts in a process of its own listens on the ports that generate_port found free, but until the
# process binds them, which takes the start of an interpreter, an outgoing connection of a test that runs at the same
# time can get one of them as its local port, and Linux does not let a server bind it then, even with SO_REUSEADDR.
# The test starts such a server again on new ports, and waits for it with a limit of time, so that a server that does
# not start fails the test instead of hanging it until the timeout of Pyjo.Prove


ATTEMPTS = 3


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
