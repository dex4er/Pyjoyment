import Pyjo.Exception
import Pyjo.Template

from Pyjo.Test import *

import html
import pathlib
import tempfile
import traceback


with subtest('A path of pathlib'):
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / 'test.ep'
        path.write_text('<%= args[0] %>\n', encoding='UTF-8')
        mt = Pyjo.Template.new()
        is_ok(mt.render_file(path, 'works'), 'works\n', 'rendered')
        is_ok(mt.name, str(path), 'name')

with subtest('A string of Python'):
    output = Pyjo.Template.new(auto_escape=True).render('<%= args[0] %>', '<b>')
    ok(isinstance(output, str), 'a str')
    is_ok(html.unescape(output), '<b>\n', 'escaped as html.escape does')
    is_ok(output.encode('UTF-8'), b'&lt;b&gt;\n', 'encoded')

with subtest('A traceback of Python'):
    output = Pyjo.Template.new().render('test\n% raise ValueError("oops")\n')
    isa_ok(output, Pyjo.Exception.object, 'exception')
    frame = output.frames[0]
    isa_ok(frame, traceback.FrameSummary, 'frame')
    is_ok((frame.filename, frame.lineno, frame.line), ('template', 2, '% raise ValueError("oops")'), 'template line')
    like_ok(''.join(traceback.format_list(output.frames[:1])), r'File "template", line 2', 'formatted')

with subtest('Modules of the standard library in a template'):
    output = Pyjo.Template.new().render("""% import datetime
% import json
<%= datetime.date(2026, 1, 2).isoformat() %> <%= json.dumps([1, 2]) %>
""")
    is_ok(output, '2026-01-02 [1, 2]\n', 'rendered')

done_testing()
