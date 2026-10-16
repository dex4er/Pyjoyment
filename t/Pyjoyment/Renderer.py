import Pyjoyment

from Pyjo.Test import *
from Pyjo.Util import gunzip

import gc
import re
import sys


# Partial rendering
app = Pyjoyment.new(secrets=['works'])
c = app.build_controller()
c.app.log.set(level='trace').unsubscribe('message')
is_ok(c.render_to_string(text='works'), b'works', 'renderer is working')

# Normal rendering with default format
renderer = c.app.renderer.set(default_format='test')


def debug(renderer, c, output, options):
    content = c.content()
    output.write(f'Hello Mojo!{content}')


renderer.add_handler('debug', debug)
c.stash()['template'] = 'something'
c.stash()['handler'] = 'debug'
is_deeply_ok(renderer.render(c), (b'Hello Mojo!', 'test'), 'normal rendering')

# Normal rendering with custom format
c.stash()['format'] = 'something'
c.stash()['template'] = 'something'
c.stash()['handler'] = 'debug'
is_deeply_ok(renderer.render(c), (b'Hello Mojo!', 'something'), 'normal rendering')

# Normal rendering with layout
del c.stash()['format']
c.stash()['template'] = 'something'
c.stash()['layout'] = 'something'
c.stash()['handler'] = 'debug'
is_deeply_ok(renderer.render(c), (b'Hello Mojo!Hello Mojo!', 'test'), 'normal rendering with layout')

# Rendering a path with dots
c.stash()['template'] = 'some.path.with.dots/template'
c.stash()['handler'] = 'debug'
is_deeply_ok(renderer.render(c), (b'Hello Mojo!', 'test'), 'rendering a path with dots')

# Unrecognized handler
with c.app.log.capture('trace') as logs:
    c.stash()['handler'] = 'not_defined'
    is_ok(renderer.render(c), None, 'return None for unrecognized handler')
like_ok(str(logs), r'No handler for "not_defined" found', 'right message')
del logs

# Default template name
c.stash(controller='foo', action='bar')
is_ok(c.app.renderer.template_for(c), 'foo/bar', 'right template name')

# Big cookie
with c.app.log.capture('trace') as logs:
    c.cookie('foo', 'x' * 4097)
like_ok(str(logs), r'Cookie "foo" is bigger than 4KiB', 'right message')
del logs

# Nested helpers
first = app.build_controller()
first.helpers.app().log.level = 'fatal'
first.app.helper('myapp.multi_level.test', lambda c: 'works!')
ok(first.app.renderer.get_helper('myapp'), 'found helper')
ok(first.app.renderer.get_helper('myapp.multi_level'), 'found helper')
ok(first.app.renderer.get_helper('myapp.multi_level.test'), 'found helper')
is_ok(first.myapp.multi_level.test(), 'works!', 'right result')
is_ok(first.helpers.myapp.multi_level.test(), 'works!', 'right result')
first.app.helper('myapp.defaults', lambda c, *args, **values: c.app.defaults(*args, **values))
ok(first.app.renderer.get_helper('myapp.defaults'), 'found helper')
is_ok(first.app.renderer.get_helper('myap.'), None, 'no helper')
is_ok(first.app.renderer.get_helper('yapp'), None, 'no helper')
first.myapp.defaults(foo='bar')
is_ok(first.myapp.defaults('foo'), 'bar', 'right result')
is_ok(first.helpers.myapp.defaults('foo'), 'bar', 'right result')
is_ok(first.app.myapp.defaults('foo'), 'bar', 'right result')
app2 = Pyjoyment.new(secrets=['works'])
second = app2.build_controller()
second.app.log.level = 'fatal'
is_ok(second.app.renderer.get_helper('myapp'), None, 'no helper')
is_ok(second.app.renderer.get_helper('myapp.defaults'), None, 'no helper')
second.app.helper('myapp.defaults', lambda c, *args, **values: 'nothing')
myapp = first.myapp
is_ok(first.myapp.defaults('foo'), 'bar', 'right result')
is_ok(second.myapp.defaults('foo'), 'nothing', 'right result')
is_ok(second.helpers.myapp.defaults('foo'), 'nothing', 'right result')
is_ok(first.myapp.defaults('foo'), 'bar', 'right result')
is_ok(first.helpers.myapp.defaults('foo'), 'bar', 'right result')

# Reuse proxy objects
helpers = first.helpers
is_ok(helpers.myapp.multi_level.test(), helpers.myapp.multi_level.test(), 'same result')

# Compression (enabled)
output = b'a' * 1000
c = app.build_controller()
c.req.headers.accept_encoding = 'gzip'
renderer.respond(c, output, 'html')
is_ok(c.res.headers.content_type, 'text/html;charset=UTF-8', 'right "Content-Type" value')
is_ok(c.res.headers.vary, 'Accept-Encoding', 'right "Vary" value')
is_ok(c.res.headers.content_encoding, 'gzip', 'right "Content-Encoding" value')
isnt_ok(c.res.body, output, 'different string')
is_ok(gunzip(c.res.body), output, 'same string')

# Compression (disabled)
renderer.compress = False
c = app.build_controller()
c.req.headers.accept_encoding = 'gzip'
renderer.respond(c, output, 'html')
is_ok(c.res.headers.content_type, 'text/html;charset=UTF-8', 'right "Content-Type" value')
ok(not c.res.headers.vary, 'no "Vary" value')
ok(not c.res.headers.content_encoding, 'no "Content-Encoding" value')
is_ok(c.res.body, output, 'same string')
renderer.compress = True

# Compression (not requested)
c = app.build_controller()
renderer.respond(c, output, 'html')
is_ok(c.res.code, 200, 'right status')
is_ok(c.res.headers.content_type, 'text/html;charset=UTF-8', 'right "Content-Type" value')
is_ok(c.res.headers.vary, 'Accept-Encoding', 'right "Vary" value')
ok(not c.res.headers.content_encoding, 'no "Content-Encoding" value')
is_ok(c.res.body, output, 'same string')

# Compression (other transfer encoding)
c = app.build_controller()
c.res.headers.content_encoding = 'whatever'
renderer.respond(c, output, 'html', 500)
is_ok(c.res.code, 500, 'right status')
is_ok(c.res.headers.content_type, 'text/html;charset=UTF-8', 'right "Content-Type" value')
is_ok(c.res.headers.vary, 'Accept-Encoding', 'right "Vary" value')
is_ok(c.res.headers.content_encoding, 'whatever', 'right "Content-Encoding" value')
is_ok(c.res.body, output, 'same string')

# Compression (below minimum length)
output = b'a' * 850
c = app.build_controller()
c.req.headers.accept_encoding = 'gzip'
renderer.respond(c, output, 'html')
is_ok(c.res.headers.content_type, 'text/html;charset=UTF-8', 'right "Content-Type" value')
ok(not c.res.headers.vary, 'no "Vary" value')
ok(not c.res.headers.content_encoding, 'no "Content-Encoding" value')
is_ok(c.res.body, output, 'same string')

with subtest('Response has already been rendered'):
    c = app.build_controller()
    c.render(text='First call')
    is_ok(c.render_to_string(text='Unrelated call'), b'Unrelated call', 'right result')
    throws_ok(lambda: c.render(text='Second call'), re.compile(r'A response has already been rendered'), 'right error')

# Missing method (AUTOLOAD)
cls = type(first.myapp)
name = re.escape(f'{cls.__module__}.{cls.__qualname__}')
throws_ok(
    lambda: first.myapp.missing,
    re.compile(rf'^Can\'t locate object method "missing" via package "{name}"'),
    'right error',
)
throws_ok(
    lambda: first.app.myapp.missing,
    re.compile(rf'^Can\'t locate object method "missing" via package "{name}"'),
    'right error',
)

# No leaky namespaces
helper_class = type(second.myapp)
is_ok(type(second.myapp), helper_class, 'same class')
ok(hasattr(helper_class, 'defaults'), 'helpers are active')
template_class = second.render_to_string(inline='<%= __name__ =%>')
is_ok(second.render_to_string(inline='<%= __name__ =%>'), template_class, 'same class')
template_module = sys.modules[template_class]
ok(hasattr(template_module, 'stash'), 'helpers are active')
del app2
gc.collect()
ok(not hasattr(helper_class, 'defaults'), 'helpers have been cleaned up')
ok(not hasattr(template_module, 'stash'), 'helpers have been cleaned up')

done_testing()
