import Pyjo.Cache
import Pyjoyment

from Pyjo.String.Template import t
from Pyjo.Test import *

import os
import tempfile


with subtest('Synopsis'):
    import Pyjoyment.Renderer

    renderer = Pyjoyment.Renderer.new()
    renderer.classes.append('MyApp.Controller.Foo')
    renderer.paths.append('/home/sri/templates')
    is_deeply_ok(renderer.classes, ['__main__', 'MyApp.Controller.Foo'], 'classes')

with subtest('cache'):
    renderer = Pyjoyment.Renderer.new()
    cache = renderer.cache
    isa_ok(cache, Pyjo.Cache.object, 'default')
    renderer.cache = Pyjo.Cache.new()

with subtest('classes'):
    renderer = Pyjoyment.Renderer.new()
    classes = renderer.classes
    is_deeply_ok(classes, ['__main__'], 'default')
    renderer.classes = ['__main__']

    # Add another class with templates in DATA section
    renderer.classes.append('Pyjoyment.Plugin.Fun')

    # Add another class with templates in DATA section and higher precedence
    renderer.classes.insert(0, 'Pyjoyment.Plugin.MoreFun')

    is_deeply_ok(renderer.classes, ['Pyjoyment.Plugin.MoreFun', '__main__', 'Pyjoyment.Plugin.Fun'], 'classes')

with subtest('compress'):
    renderer = Pyjoyment.Renderer.new()
    boolean = renderer.compress
    is_ok(boolean, True, 'default')
    renderer.compress = False

with subtest('default_format'):
    renderer = Pyjoyment.Renderer.new()
    default = renderer.default_format
    is_ok(default, 'html', 'default')
    renderer.default_format = 'html'

with subtest('default_handler'):
    renderer = Pyjoyment.Renderer.new()
    default = renderer.default_handler
    is_ok(default, None, 'default')
    renderer.default_handler = 'ep'

with subtest('encoding'):
    renderer = Pyjoyment.Renderer.new()
    encoding = renderer.encoding
    is_ok(encoding, 'UTF-8', 'default')
    renderer.encoding = 'koi8-r'

with subtest('handlers'):
    renderer = Pyjoyment.Renderer.new()
    handlers = renderer.handlers
    is_deeply_ok(handlers, {}, 'default')
    renderer.handlers = {'epl': lambda renderer, c, output, options: ...}

with subtest('helpers'):
    renderer = Pyjoyment.Renderer.new()
    helpers = renderer.helpers
    is_deeply_ok(helpers, {}, 'default')
    renderer.helpers = {'url_for': lambda c, *args: ...}

with subtest('min_compress_size'):
    renderer = Pyjoyment.Renderer.new()
    size = renderer.min_compress_size
    is_ok(size, 860, 'default')
    renderer.min_compress_size = 1024

with subtest('paths'):
    renderer = Pyjoyment.Renderer.new()
    paths = renderer.paths
    is_deeply_ok(paths, [], 'default')
    renderer.paths = ['/home/sri/templates']

    # Add another "templates" directory
    renderer.paths.append('/home/sri/templates')

    # Add another "templates" directory with higher precedence
    renderer.paths.insert(0, '/home/sri/themes/blue/templates')

    is_ok(renderer.paths[0], '/home/sri/themes/blue/templates', 'higher precedence')

with subtest('templates'):
    renderer = Pyjoyment.Renderer.new()
    templates = renderer.templates
    is_deeply_ok(templates, {}, 'default')
    renderer.templates = {'index.html': lambda c: t('<p>Hello!</p>')}

with subtest('accepts'):
    app = Pyjoyment.new()
    c = app.build_controller()
    c.req.headers.accept = 'application/json'
    all = app.renderer.accepts(c)
    is_deeply_ok(all, ['json'], 'all')
    best = app.renderer.accepts(c, 'html', 'json')
    is_ok(best, 'json', 'best')

with subtest('add_handler'):
    renderer = Pyjoyment.Renderer.new()
    renderer = renderer.add_handler('epl', lambda renderer, c, output, options: ...)

    def foo(renderer, c, output, options):
        ...
        output.write('Hello World!')

    renderer.add_handler('foo', foo)

    app = Pyjoyment.new()
    app.renderer = renderer
    c = app.build_controller()
    is_ok(c.render_to_string(handler='foo', template='bar'), 'Hello World!', 'handler')

with subtest('add_helper'):
    renderer = Pyjoyment.Renderer.new()
    renderer = renderer.add_helper('url_for', lambda c, *args: ...)

    def foo(c, *args): ...

    renderer.add_helper('foo', foo)
    is_ok(renderer.get_helper('foo'), foo, 'helper')

with subtest('add_template'):
    renderer = Pyjoyment.Renderer.new()
    renderer = renderer.add_template('index.html', lambda c: t('<p>Hello!</p>'))

    @renderer.add_template('index.html')
    def index(c): ...

    is_ok(renderer.templates['index.html'], index, 'decorator')

    def foo(c, name):
        return t('<p>Hello {name}!</p>')

    renderer.add_template('foo.html', foo)

    app = Pyjoyment.new()
    app.log.level = 'fatal'
    app.renderer.add_template('foo.html', foo)
    c = app.build_controller()
    is_ok(c.render_to_string('foo', name='Joe'), '<p>Hello Joe!</p>', 'template')

with subtest('get_data_template'):
    renderer = Pyjoyment.Renderer.new()
    template = renderer.get_data_template({'template': 'foo/bar', 'format': 'html', 'handler': 'epl'})
    is_ok(template, None, 'no template')

with subtest('get_helper'):
    renderer = Pyjoyment.Renderer.new()
    renderer.add_helper('url_for', lambda c, *args: 'url')
    helper = renderer.get_helper('url_for')
    is_ok(helper(None), 'url', 'helper')

with subtest('render'):
    app = Pyjoyment.new()
    c = app.build_controller()
    c.stash(text='Hello')
    output, format = app.renderer.render(Pyjoyment.Controller.new(app=app, stash=c.stash(), tx=c.tx))
    is_deeply_ok([output, format], [b'Hello', 'html'], 'output and format')

with subtest('respond'):
    app = Pyjoyment.new()
    app.log.level = 'fatal'
    c = app.build_controller()
    boolean = app.renderer.respond(c, b'output', 'txt')
    is_ok(boolean, True, 'responded')
    c = app.build_controller()
    boolean = app.renderer.respond(c, b'output', 'txt', 201)
    is_ok(c.res.code, 201, 'status')

with subtest('template_for'):
    app = Pyjoyment.new()
    c = app.build_controller().stash(controller='foo', action='bar')
    name = app.renderer.template_for(c)
    is_ok(name, 'foo/bar', 'name')

with subtest('template_handler'):
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, 'foo'))
        open(os.path.join(tmp, 'foo', 'bar.html.ep'), 'w').close()
        renderer = Pyjoyment.Renderer.new()
        renderer.paths.append(tmp)
        handler = renderer.template_handler({'template': 'foo/bar', 'format': 'html'})
        is_ok(handler, 'ep', 'handler')

with subtest('template_name'):
    renderer = Pyjoyment.Renderer.new()
    template = renderer.template_name({'template': 'foo/bar', 'format': 'html', 'handler': 'epl'})
    is_ok(template, 'foo/bar.html.epl', 'name')

with subtest('template_path'):
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, 'foo'))
        open(os.path.join(tmp, 'foo', 'bar.html.epl'), 'w').close()
        renderer = Pyjoyment.Renderer.new()
        renderer.paths.append(tmp)
        path = renderer.template_path({'template': 'foo/bar', 'format': 'html', 'handler': 'epl'})
        is_ok(path, os.path.join(tmp, 'foo', 'bar.html.epl'), 'path')

with subtest('warmup'):
    renderer = Pyjoyment.Renderer.new()
    renderer.warmup()
    is_ok(renderer.template_handler({'template': 'foo', 'format': 'html'}), None, 'no templates')

done_testing()
