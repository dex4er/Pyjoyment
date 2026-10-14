import Pyjo.Asset.File
import Pyjo.Upload

from Pyjo.Test import *

import pathlib
import tempfile


with subtest('pathlib'):
    with tempfile.TemporaryDirectory() as dir:
        upload = Pyjo.Upload.new(asset=Pyjo.Asset.File.new().add_chunk(b'uploaded'), filename='foo.txt')
        target = pathlib.Path(dir) / upload.filename
        is_ok(upload.move_to(target), upload, 'returns the upload')
        is_ok(target.read_bytes(), b'uploaded', 'moved to a pathlib.Path')
        is_ok(upload.size, 8, 'size after the move')

done_testing()
