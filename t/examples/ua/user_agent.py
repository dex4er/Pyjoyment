import Pyjo.File

from Pyjo.Test import *

import importlib
import os
import signal
import subprocess
import sys
import tempfile


# The example itself, on the port 3000 replaced by a free one, in a process of its own: its timer requests the server
# every second, until INT stops the server gracefully, which the requests of the timer do not keep from stopping
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
ServerStart = importlib.import_module('ServerStart')

ROOT = Pyjo.File.curfile().dirname().dirname().dirname().dirname().to_str()
SOURCE = Pyjo.File.path(ROOT, 'examples', 'ua', 'user_agent.py').slurp('UTF-8')

with tempfile.TemporaryDirectory() as dir:
    log = os.path.join(dir, 'output.log')

    def start():
        port = ServerStart.port()
        script = os.path.join(dir, 'user_agent.py')
        Pyjo.File.path(script).spew(SOURCE.replace('3000', str(port)), 'UTF-8')
        # A group of its own on Windows, which Ctrl-Break reaches
        with open(log, 'w') as output:
            process = subprocess.Popen(
                [sys.executable, '-u', script],
                env={**os.environ, 'PYTHONPATH': ROOT},
                stdout=output,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0,
            )
        if ServerStart.listening(port, process):
            return process
        process.wait()
        return None

    process = ServerStart.retry(start)

    def responses():
        return Pyjo.File.path(log).slurp('UTF-8').splitlines().count('200 Your Pyjo is working!')

    try:
        ServerStart.wait_for(lambda: responses() >= 2 or process.poll() is not None, 'two responses')
    finally:
        # Windows sends no INT to one process, and Ctrl-Break stops the server, immediately
        process.send_signal(signal.CTRL_BREAK_EVENT if sys.platform == 'win32' else signal.SIGINT)
        try:
            process.wait(10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    ok(responses() >= 2, 'the timer requests the server every second')
    is_ok(process.returncode, 0, 'INT stops the server gracefully')

done_testing()
