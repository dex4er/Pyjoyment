from Pyjo.Test import *

import http.client
import os
import pathlib
import signal
import socket
import subprocess
import sys
import tempfile
import time


if not hasattr(os, 'fork'):
    plan(skip_all='no os.fork')

# PyPy with its JIT on macOS: the child of a fork crashes now and then with a bus error, under load
if sys.platform == 'darwin' and getattr(sys, 'pypy_translation_info', {}).get('translation.jit'):
    plan(skip_all='PyPy with its JIT on macOS: the child of a fork crashes now and then with SIGBUS')

import Pyjo.IOLoop.Server


ROOT = os.path.join(os.path.dirname(__file__), '..', '..')


# The lines that the manager prints about its workers, until one matches
def until(process, prefix):
    lines = []
    while line := process.stdout.readline():
        lines.append(line.strip())
        if line.startswith(prefix):
            break
    return lines


with subtest('Signals, the process id file and http.client'), tempfile.TemporaryDirectory() as dir:
    port = Pyjo.IOLoop.Server.object.generate_port()
    pid_file = pathlib.Path(dir, 'prefork.pid')
    process = subprocess.Popen(
        [
            sys.executable,
            '-c',
            f"""
import os, Pyjo.Server.Prefork

prefork = Pyjo.Server.Prefork.new(
    heartbeat_interval=0.1, listen=['http://127.0.0.1:{port}'], pid_file={str(pid_file)!r}, silent=True, workers=2
)
prefork.app.log.level = 'fatal'
prefork.on('spawn', lambda prefork, pid: print('spawn', pid, flush=True))
prefork.on('reap', lambda prefork, pid: print('reap', pid, flush=True))
prefork.on('finish', lambda prefork, graceful: print('finish', graceful, flush=True))


@prefork.unsubscribe('request').on('request')
def request(prefork, tx):
    tx.res.code = 200
    tx.res.body = str(os.getpid()).encode()
    tx.resume()


prefork.run()
print('stopped', flush=True)
""",
        ],
        env=dict(os.environ, PYTHONPATH=ROOT),
        stdout=subprocess.PIPE,
        text=True,
    )
    spawned = until(process, 'spawn') + until(process, 'spawn')
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            socket.create_connection(('127.0.0.1', port), 0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    is_ok(len(spawned), 2, 'two workers')

    deadline = time.monotonic() + 10
    while not pid_file.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    is_ok(int(pid_file.read_text()), process.pid, 'process id file of the manager')

    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
    conn.request('GET', '/')
    worker = int(conn.getresponse().read())
    conn.close()
    ok(f'spawn {worker}' in spawned, 'served by a worker')

    process.send_signal(signal.SIGTTIN)
    ok(until(process, 'spawn')[-1].startswith('spawn'), 'TTIN spawns one more worker')
    process.send_signal(signal.SIGTTOU)
    ok(until(process, 'reap')[-1].startswith('reap'), 'TTOU stops one worker')

    process.send_signal(signal.SIGTERM)
    lines = until(process, 'stopped')
    is_ok(lines[0], 'finish False', 'TERM stops the server immediately')
    is_ok(len([line for line in lines if line.startswith('reap')]), 2, 'the workers have been reaped')
    is_ok(process.wait(30), 0, 'exit status')
    process.stdout.close()
    ok(not pid_file.exists(), 'process id file has been removed')

done_testing()
