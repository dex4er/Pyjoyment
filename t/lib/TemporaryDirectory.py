import errno
import shutil
import tempfile

from contextlib import contextmanager


@contextmanager
def TemporaryDirectory():
    name = tempfile.mkdtemp()
    try:
        yield name
    finally:
        try:
            shutil.rmtree(name)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
