import Pyjo.Server.Prethread

from Pyjo.File import tempdir
from Pyjo.Test import *

import os
import signal
import subprocess
import sys
import time


with subtest('The process id file of a process that runs'):
    file = tempdir().child('prethread.pid')
    prethread = Pyjo.Server.Prethread.new(pid_file=file)
    prethread.ensure_pid_file(os.getpid())

    # On Windows, the check sends no Ctrl-C to the processes of the console, which os.kill with 0 does there, and which
    # the console delivers by the time a process starts in it
    interrupted = []
    handler = signal.signal(signal.SIGINT, lambda signum, frame: interrupted.append(signum))
    try:
        is_ok(prethread.check_pid(), os.getpid(), 'right process id')
        subprocess.run([sys.executable, '-c', 'pass'])
        time.sleep(0.2)
    finally:
        signal.signal(signal.SIGINT, handler)
    is_deeply_ok(interrupted, [], 'no Ctrl-C')
    ok(os.path.exists(file), 'file kept')

with subtest('The process id file of a process that has ended'):
    file = tempdir().child('prethread.pid')
    process = subprocess.Popen([sys.executable, '-c', 'pass'])
    process.wait()
    prethread = Pyjo.Server.Prethread.new(pid_file=file)
    prethread.ensure_pid_file(process.pid)
    is_ok(prethread.check_pid(), None, 'not running')
    ok(not os.path.exists(file), 'file removed')

done_testing()
