"""
__DATA__
@@ layouts/green.html.ep
Green<%= content() %>

@@ dead_template.html.ep
% raise Exception('dead template!')

@@ dead_template_too.xml.epl
% raise Exception('dead template too!')

@@ dead_included_template.html.ep
this
%= include('dead_template')
works!

@@ dead_template_with_layout.html.ep
% c.layout('green')
% raise Exception('dead template with layout!')

@@ exception.development.xml.ep
<very>bad</very>

@@ dead_helper.html.ep
% dead_helper()
"""

import Pyjo.Base
import Pyjo.Exception
import Pyjo.Test.Pyjo

from Pyjo.Test import *
from Pyjoyment.Lite import app, get, helper, hook

import os
import re


# BEGIN { $ENV{MOJO_MODE} = 'development' }, before the mode of the application is read
os.environ['PYJO_MODE'] = 'development'

# Left out from Mojolicious: MOJO_REACTOR, as the tests run on the reactor of Pyjo.Reactor.detect()

# Not in Mojolicious: the templates of the DATA section are in the docstring, as the requests come before the end of
# the script

# Perl's die with a string is raise in Python, which is a statement, so the actions that die are functions

# No real templates
app.renderer.paths[0] = app.home.child('does_not_exist')

# Logger
app.log.handle = None
app.log.level = os.environ['PYJO_LOG_LEVEL'] = 'debug'
log = ''


@app.log.on('message')
def message(_, *args):
    global log
    log += ':'.join(map(str, args))


@helper('dead_helper')
def dead_helper(c):
    raise Exception('dead helper!\n')


def dead(*args):
    raise Exception('dead handler!\n')


app.renderer.add_handler('dead', dead)


# Custom rendering for missing "txt" template
@hook('before_render')
def before_render_missing(c, args):
    if (args.get('template') or '') != 'exception.development':
        return
    stash = c.stash()
    exception = stash['snapshot'].get('exception')
    if args['format'] == 'txt':
        args['text'] = f'Missing template, {exception}.'


# Custom exception rendering for "txt"
@hook('before_render')
def before_render_txt(c, args):
    if (args.get('template') or '') != 'exception':
        return
    if not c.accepts('', 'txt'):
        return
    args['text'], args['format'] = c.stash()['exception'], 'txt'


@get('/logger')
def logger(c):
    level = c.param('level')
    msg = c.param('message')
    getattr(c.app.log, level)(msg)
    c.render(text=f'{level}: {msg}')


@get('/custom_exception')
def custom_exception(c):
    # Python raises only exceptions, so the object is the argument of one
    raise Exception(Pyjo.Base.new())


get('/dead_template')

get('/dead_template_too', format=['xml'])

get('/dead_handler', {'handler': 'dead'}, format=['xml'])


@get('/dead_action_epl', {'handler': 'epl'}, format=['xml'])
def dead_action_epl(c):
    raise Exception('dead action epl!\n')


get('/dead_included_template')

get('/dead_template_with_layout')


@get('/dead_action', {'format': None}, format=['xml', 'json'])
def dead_action(c):
    raise Exception('dead action!\n')


@get('/double_dead_action_☃')
def double_dead_action(c):
    try:
        raise Exception('double dead action!')
    except Exception as e:
        raise e


@get('/trapped')
def trapped(c):
    try:
        raise Exception({'foo': 'bar'})
    except Exception as e:
        c.render(text=e.args[0].get('foo') or 'failed')


get('/missing_template', {'exception': 'whatever', 'format': None}, format=['xml', 'json', 'txt'])


@get('/missing_template/too')
def missing_template_too(c):
    c.render('does_not_exist')


get('/missing_helper', lambda c: c.missing_helper())


# Dummy exception object
class MyException(Exception):
    def __init__(self, error=None):
        self.error = error

    def __str__(self):
        return self.error


@get('/trapped/too')
def trapped_too(c):
    try:
        raise MyException(error='works')
    except Exception as e:
        c.render(text=str(e) or 'failed')


# Reuse exception and snapshot
exception = snapshot = None


@hook('after_dispatch')
def after_dispatch(c):
    global exception, snapshot
    if not c.req.url.path.contains('/reuse/exception'):
        return
    exception = c.stash('exception')
    snapshot = c.stash('snapshot')


# Custom exception handling
@hook('around_dispatch')
def around_dispatch(next, c):
    try:
        next()
    except Exception as e:
        if not re.match(r'^CUSTOM\n', str(e)):
            raise
        c.render(text='Custom handling works!')


@get('/reuse/exception', {'foo': 'bar'})
def reuse_exception(c):
    raise Exception('Reusable exception.\n')


@get('/custom')
def custom(c):
    raise Exception('CUSTOM\n')


@get('/txt/exception')
def txt_exception(c):
    c.exception_format('txt').res.headers.header('X-Text', c.exception_format())
    raise Exception('Text exception')


get('/dead_helper')

t = Pyjo.Test.Pyjo.new()

with subtest('Missing error'):
    c = t.app.build_controller()
    c.reply.exception(None)
    like_ok(c.res.text, r'Exception!', 'right result')

    c = t.app.build_controller()
    c.reply.exception()
    like_ok(c.res.text, r'Exception!', 'right result')

    c = t.app.build_controller()
    c.reply.exception(Pyjo.Exception.new())
    like_ok(c.res.text, r'Exception!', 'right result')

with subtest('Debug'):
    t.get_ok('/logger?level=debug&message=one').status_is(200).content_is('debug: one')
    like_ok(log, r'debug:one', 'right result')

with subtest('Info'):
    t.get_ok('/logger?level=info&message=two').status_is(200).content_is('info: two')
    like_ok(log, r'info:two', 'right result')

with subtest('Warn'):
    t.get_ok('/logger?level=warn&message=three').status_is(200).content_is('warn: three')
    like_ok(log, r'warn:three', 'right result')

with subtest('Error'):
    t.get_ok('/logger?level=error&message=four').status_is(200).content_is('error: four')
    like_ok(log, r'error:four', 'right result')

with subtest('Fatal'):
    t.get_ok('/logger?level=fatal&message=five').status_is(200).content_is('fatal: five')
    like_ok(log, r'fatal:five', 'right result')

with subtest('"debug.html.ep" route suggestion'):
    t.get_ok('/does_not_exist').status_is(404).element_exists('nav').content_like(r'/does_not_exist')

with subtest('"debug.html.ep" route suggestion'):
    t.post_ok('/does_not_exist').status_is(404).content_like(r'/does_not_exist')

with subtest('Custom exception'):
    t.get_ok('/custom_exception').status_is(500).content_like(r'Pyjo\.Base')

with subtest('Dead template'):
    t.get_ok('/dead_template').status_is(500).content_like(r'dead template!').content_like(r'line 1')
    like_ok(log, r'dead template!', 'right result')

with subtest('Dead template with a different handler'):
    t.get_ok('/dead_template_too.xml').status_is(500).content_is('<very>bad</very>\n')
    like_ok(log, r'dead template too!', 'right result')

with subtest('Dead handler'):
    t.get_ok('/dead_handler.xml').status_is(500).content_is('<very>bad</very>\n')
    like_ok(log, r'dead handler!', 'right result')

with subtest('Dead action (with a different handler)'):
    t.get_ok('/dead_action_epl.xml').status_is(500).content_is('<very>bad</very>\n')
    like_ok(log, r'dead action epl!', 'right result')

with subtest('Dead included template'):
    t.get_ok('/dead_included_template').status_is(500).content_like(r'dead template!').content_like(r'line 1')

with subtest('Dead template with layout'):
    (
        t.get_ok('/dead_template_with_layout')
        .status_is(500)
        .content_like(r'dead template with layout!')
        .content_like(r'line 2')
        .content_unlike(r'Green')
    )
    like_ok(log, r'dead template with layout!', 'right result')

with subtest('Dead action'):
    (
        t.get_ok('/dead_action')
        .status_is(500)
        .content_type_is('text/html;charset=UTF-8')
        .content_like(r'get\(&#39;/dead_action&#39;')
        .content_like(r'dead action!')
        .text_is('#error', 'dead action!\n')
    )
    like_ok(log, r'dead action!', 'right result')

with subtest('Dead action with different format'):
    t.get_ok('/dead_action.xml').status_is(500).content_type_is('application/xml').content_is('<very>bad</very>\n')

with subtest('Dead action with unsupported format'):
    (
        t.get_ok('/dead_action.json')
        .status_is(500)
        .content_type_is('text/html;charset=UTF-8')
        .content_like(r'get\(&#39;/dead_action&#39;')
        .content_like(r'dead action!')
    )

with subtest('Dead action with custom exception rendering'):
    (
        t.get_ok('/dead_action', {'Accept': 'text/plain'})
        .status_is(500)
        .content_type_is('text/plain;charset=UTF-8')
        .content_like(r'^dead action!\n')
    )

with subtest('Action dies twice'):
    (
        t.get_ok('/double_dead_action_☃')
        .status_is(500)
        .content_like(r'get\(&#39;/double_dead_action_☃&#39;\)')
        .content_like(r'File.+lite_app\.py", line \d')
        .content_like(r'double dead action!')
    )

with subtest('Trapped exception'):
    t.get_ok('/trapped').status_is(200).content_is('bar')

with subtest('Another trapped exception'):
    t.get_ok('/trapped/too').status_is(200).content_is('works')

with subtest('Custom exception handling'):
    t.get_ok('/custom').status_is(200).content_is('Custom handling works!')

with subtest('Exception in helper'):
    t.get_ok('/dead_helper').status_is(500).content_like(r'dead helper!')

with subtest('Missing template'):
    (
        t.get_ok('/missing_template')
        .status_is(500)
        .content_type_is('text/html;charset=UTF-8')
        .content_like(r'Route without action and nothing to render')
    )

with subtest('Missing template with different format'):
    (
        t.get_ok('/missing_template.xml')
        .status_is(500)
        .content_type_is('application/xml')
        .content_is('<very>bad</very>\n')
    )

with subtest('Missing template with unsupported format'):
    (
        t.get_ok('/missing_template.json')
        .status_is(500)
        .content_type_is('text/html;charset=UTF-8')
        .content_like(r'Route without action and nothing to render')
    )

with subtest('Missing template with custom rendering'):
    (
        t.get_ok('/missing_template.txt')
        .status_is(500)
        .content_type_is('text/plain;charset=UTF-8')
        .content_is('Missing template, whatever.')
    )

with subtest('Missing template (failed rendering)'):
    (
        t.get_ok('/missing_template/too')
        .status_is(500)
        .content_type_is('text/html;charset=UTF-8')
        .content_like(r'Could not render a response')
    )

with subtest('Missing helper (correct context)'):
    (
        t.get_ok('/missing_helper')
        .status_is(500)
        .content_type_is('text/html;charset=UTF-8')
        .content_like(r'Server Error')
        .content_like(r'lambda c: c\.missing_helper\(\)')
    )

with subtest('Reuse exception'):
    ok(not exception, 'no exception')
    ok(not snapshot, 'no snapshot')
    t.get_ok('/reuse/exception').status_is(500).content_like(r'Reusable exception')
    isa_ok(exception, Pyjo.Exception.object, 'right exception')
    like_ok(str(exception), r'Reusable exception', 'right message')
    is_ok(snapshot['foo'], 'bar', 'right snapshot value')
    ok(not snapshot.get('exception'), 'no exception in snapshot')

with subtest('JSON exceptions'):
    t.app.mode = 'development'
    t.app.exception_format = 'json'
    is_ok(t.app.exception_format, 'json', 'right exception format')
    (
        t.get_ok('/dead_template')
        .status_is(500)
        .content_type_is('application/json;charset=UTF-8')
        .json_like('/error', r'dead template!')
    )
    (
        t.get_ok('/does_not_exist')
        .status_is(404)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'error': 'Not Found'})
    )
    stash = None

    @t.app.hook('after_dispatch')
    def after_dispatch_json(c):
        global stash
        stash = c.stash()

    (
        t.get_ok('/txt/exception')
        .status_is(500)
        .header_is('X-Text', 'txt')
        .content_type_is('text/plain;charset=UTF-8')
        .content_like(r'Text exception')
    )
    ok(stash['exception'], 'exception exists in stash')
    isa_ok(stash['exception'], Pyjo.Exception.object, 'is stash exception correct type?')

    t.app.mode = 'production'
    (
        t.get_ok('/dead_template')
        .status_is(500)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'error': 'Internal Server Error'})
    )
    (
        t.get_ok('/does_not_exist')
        .status_is(404)
        .content_type_is('application/json;charset=UTF-8')
        .json_is({'error': 'Not Found'})
    )

with subtest('Text exceptions'):
    t.app.mode = 'development'
    t.app.exception_format = 'txt'
    is_ok(t.app.exception_format, 'txt', 'right exception format')
    (
        t.get_ok('/dead_template')
        .status_is(500)
        .content_type_is('text/plain;charset=UTF-8')
        .content_like(r'dead template!')
    )
    t.get_ok('/does_not_exist').status_is(404).content_type_is('text/plain;charset=UTF-8').content_is('Not Found')
    stash = None

    @t.app.hook('after_dispatch')
    def after_dispatch_txt(c):
        global stash
        stash = c.stash()

    (
        t.get_ok('/txt/exception')
        .status_is(500)
        .header_is('X-Text', 'txt')
        .content_type_is('text/plain;charset=UTF-8')
        .content_like(r'Text exception')
    )
    ok(stash['exception'], 'exception exists in stash')
    isa_ok(stash['exception'], Pyjo.Exception.object, 'is stash exception correct type?')

    t.app.mode = 'production'
    (
        t.get_ok('/dead_template')
        .status_is(500)
        .content_type_is('text/plain;charset=UTF-8')
        .content_is('Internal Server Error')
    )
    t.get_ok('/does_not_exist').status_is(404).content_type_is('text/plain;charset=UTF-8').content_is('Not Found')

# Renamed from Mojolicious: the bundled files are in pyjo/, where Mojo has them in mojo/, the language of highlight.js
# is pyjoyment.min.js, where Mojo has mojolicious.min.js, and the images of the unicat are failunicat.png and
# nounicat.png, where Mojo has failraptor.png and noraptor.png
with subtest('Bundled static files'):
    t.get_ok('/pyjo/highlight.js/highlight.min.js').status_is(200).content_type_is('application/javascript')
    t.get_ok('/pyjo/highlight.js/pyjoyment.min.js').status_is(200).content_type_is('application/javascript')
    t.get_ok('/pyjo/highlight.js/highlight-mojo-dark.css').status_is(200).content_type_is('text/css')

    t.get_ok('/pyjo/bootstrap/bootstrap.js').status_is(200).content_type_is('application/javascript')
    t.get_ok('/pyjo/bootstrap/bootstrap.css').status_is(200).content_type_is('text/css')

    t.get_ok('/pyjo/failunicat.png').status_is(200).content_type_is('image/png')
    t.get_ok('/pyjo/logo.png').status_is(200).content_type_is('image/png')
    t.get_ok('/pyjo/logo-white.png').status_is(200).content_type_is('image/png')
    t.get_ok('/pyjo/logo-white-2x.png').status_is(200).content_type_is('image/png')
    t.get_ok('/pyjo/nounicat.png').status_is(200).content_type_is('image/png')
    t.get_ok('/pyjo/notfound.png').status_is(200).content_type_is('image/png')
    t.get_ok('/pyjo/pinstripe-dark.png').status_is(200).content_type_is('image/png')
    t.get_ok('/pyjo/pinstripe-light.png').status_is(200).content_type_is('image/png')

done_testing()
