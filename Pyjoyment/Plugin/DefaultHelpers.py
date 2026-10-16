"""
Pyjoyment.Plugin.DefaultHelpers - Default helpers plugin
========================================================
::

    # Pyjoyment
    app.plugin('DefaultHelpers')

:mod:`Pyjoyment.Plugin.DefaultHelpers` is a collection of helpers for
:mod:`Pyjoyment`.

This is a core plugin, that means it is always enabled and its code a good
example for learning to build new plugins, you're welcome to fork it.

See :mod:`Pyjoyment.Plugins` for a list of plugins that are available by
default.

Helpers
-------

:mod:`Pyjoyment.Plugin.DefaultHelpers` implements the following helpers.

accepts ::

    formats = c.accepts()
    format = c.accepts('html', 'json', 'txt')

Select best possible representation for resource from ``format``
``GET``/``POST`` parameter, ``format`` stash value or ``Accept`` request header
with :meth:`Pyjoyment.Renderer.Pyjoyment_Renderer.accepts`, defaults to
returning the first extension if no preference could be detected. ::

    # Check if JSON is acceptable
    if c.accepts('json'):
        c.render(json={'hello': 'world'})

    # Check if JSON was specifically requested
    if c.accepts('', 'json'):
        c.render(json={'hello': 'world'})

    # Unsupported representation
    if not (format := c.accepts('html', 'json')):
        c.render(data=b'', status=204)

    # Detected representations to select from
    formats = c.accepts()

app ::

    %= app().secrets[0]

Alias for :attr:`Pyjoyment.Controller.Pyjoyment_Controller.app`.

b ::

    %= b(b'Joel is a slug').slugify()

Turn bytes into a :mod:`Pyjo.String.Bytes` object.

c ::

    %= c.c('a', 'b', 'c').shuffle().join()

Turn list into a :mod:`Pyjo.Collection` object. In templates, the variable
``c`` is the controller, which hides the helper.

config ::

    %= config('something')

Alias for :meth:`Pyjoyment.Pyjoyment_App.config`.

content ::

    %= content('foo', begin
      test
    % end)
    %= content('bar', 'Hello World!')
    %= content('foo')
    %= content('bar')
    %= content()

Store partial rendered content in a named buffer and retrieve it later,
defaults to retrieving the named buffer ``content``, which is used by the
renderer for the ``layout`` and ``extends`` features. New content will be
ignored if the named buffer is already in use.

content_for ::

    % content_for('foo', begin
      test
    % end)
    %= content_for('foo')

Same as ``content``, but appends content to named buffers if they are already
in use. ::

    % content_for('message', begin
      Hello
    % end)
    % content_for('message', begin
      world!
    % end)
    %= content('message')

content_with ::

    % content_with('foo', begin
      test
    % end)
    %= content_with('foo')

Same as ``content``, but replaces content of named buffers if they are already
in use. ::

    % content('message', begin
      world!
    % end)
    % content_with('message', begin
      Hello <%= content('message') %>
    % end)
    %= content('message')

csrf_token ::

    %= csrf_token()

Get CSRF token from ``session``, and generate one if none exists. The token is
masked with a fresh random value on every call to protect against BREACH
attacks.

current_route ::

    % if current_route('login'):
      Welcome to Pyjoyment!
    % end
    %= current_route()

Check or get name of current route.

dumper ::

    %= dumper({'some': 'data'})

Dump a Python data structure with :func:`Pyjo.Util.dumper`, very useful for
debugging.

exception_format ::

    format = c.exception_format()
    c = c.exception_format('txt')

Format for HTTP exceptions (``html``, ``json``, or ``txt``), defaults to the
value of :attr:`Pyjoyment.Pyjoyment_App.exception_format`.

extends ::

    % extends('blue')
    % extends('blue', title='Blue!')

Set ``extends`` stash value, all additional keyword arguments get merged into
the ``stash``.

flash ::

    foo = c.flash('foo')
    c = c.flash({'foo': 'bar'})
    c = c.flash(foo='bar')
    %= flash('foo')

Data storage persistent only for the next request, stored in the ``session``. ::

    # Show message after redirect
    c.flash(message='User created successfully!')
    c.redirect_to('show_user', id=23)

inactivity_timeout ::

    c = c.inactivity_timeout(3600)

Use :func:`Pyjo.IOLoop.stream` to find the current connection and increase
timeout if possible. ::

    # Longer version
    Pyjo.IOLoop.stream(c.tx.connection).timeout = 3600

include ::

    %= include('menubar')
    %= include('menubar', format='txt')

Alias for :meth:`Pyjoyment.Controller.Pyjoyment_Controller.render_to_string`.

layout ::

    % layout('green')
    % layout('green', title='Green!')

Set ``layout`` stash value, all additional keyword arguments get merged into
the ``stash``.

log ::

    log = c.log()

Alternative to :attr:`Pyjoyment.Pyjoyment_App.log` that includes
:attr:`Pyjo.Message.Request.Pyjo_Message_Request.request_id` with every log
message. ::

    # Log message with context
    c.log().debug('This is a log message with request id')

    # Pass logger with context to model
    log = c.log()
    c.some_model().create({'foo': foo}, log)

param ::

    %= param('foo')

Alias for :meth:`Pyjoyment.Controller.Pyjoyment_Controller.param`.

redirect_to ::

    c = c.redirect_to('named', foo='bar')
    c = c.redirect_to('named', {'foo': 'bar'})
    c = c.redirect_to('/index.html')
    c = c.redirect_to('http://example.com/index.html')

Prepare a ``302`` (if the status code is not already ``3xx``) redirect response
with ``Location`` header, takes the same arguments as ``url_for``. ::

    # Moved Permanently
    c.res.code = 301
    c.redirect_to('some_route')

    # Temporary Redirect
    c.res.code = 307
    c.redirect_to('some_route')

reply.exception ::

    c = c.reply.exception('Oops!')
    c = c.reply.exception(Pyjo.Exception.new())

Render an exception response in the appropriate format by delegating to more
specific exception helpers.

reply.html_exception ::

    c = c.reply.html_exception('Oops!')
    c = c.reply.html_exception(Pyjo.Exception.new())

Render the exception template ``exception.$mode.$format.*`` or
``exception.$format.*`` and set the response status code to ``500``. Also sets
the stash values ``exception`` to a :mod:`Pyjo.Exception` object and
``snapshot`` to a copy of the ``stash`` for use in the templates.

reply.html_not_found ::

    c = c.reply.html_not_found()

Render the not found template ``not_found.$mode.$format.*`` or
``not_found.$format.*`` and set the response status code to ``404``. Also sets
the stash value ``snapshot`` to a copy of the ``stash`` for use in the
templates.

reply.json_exception ::

    c = c.reply.json_exception('Oops!')
    c = c.reply.json_exception(Pyjo.Exception.new())

Render a JSON response and set the response status to ``500``.

reply.json_not_found ::

    c = c.reply.json_not_found()

Render a JSON response and set the response status to ``404``.

reply.not_found ::

    c = c.reply.not_found()

Render a not found response in the appropriate format by delegating to more
specific exception helpers.

reply.txt_exception ::

    c = c.reply.txt_exception('Oops!')
    c = c.reply.txt_exception(Pyjo.Exception.new())

Render a plain text response and set the response status to ``500``.

reply.txt_not_found ::

    c = c.reply.txt_not_found()

Render a plain text response and set the response status to ``404``.

respond_to ::

    c = c.respond_to(json={'json': {'message': 'Welcome!'}}, html={'template': 'welcome'}, any=lambda c: ...)

Automatically select best possible representation for resource from ``format``
``GET``/``POST`` parameter, ``format`` stash value or ``Accept`` request
header, defaults to
:attr:`Pyjoyment.Renderer.Pyjoyment_Renderer.default_format` or rendering an
empty ``204`` response. Each representation can be handled with a callback or
a dict containing arguments to be passed to
:meth:`Pyjoyment.Controller.Pyjoyment_Controller.render`. ::

    # Everything else than "json" and "xml" gets a 204 response
    c.respond_to(
        json=lambda c: c.render(json={'just': 'works'}),
        xml={'text': '<just>works</just>'},
        any={'data': b'', 'status': 204},
    )

For more advanced negotiation logic you can also use ``accepts``.

session ::

    %= session('foo')

Alias for :meth:`Pyjoyment.Controller.Pyjoyment_Controller.session`.

stash ::

    %= stash('foo')
    % stash(foo='bar')

Alias for :meth:`Pyjoyment.Controller.Pyjoyment_Controller.stash`. ::

    %= stash('name') or 'Somebody'

timing.begin ::

    c.timing.begin('foo')

Create named timestamp for ``timing.elapsed``.

timing.elapsed ::

    elapsed = c.timing.elapsed('foo')

Return fractional amount of time in seconds since named timstamp has been
created with ``timing.begin`` or ``None`` if no such timestamp exists. ::

    # Log timing information
    c.timing.begin('database_stuff')
    ...
    elapsed = c.timing.elapsed('database_stuff')
    c.app.log.debug(f'Database stuff took {elapsed} seconds')

timing.rps ::

    rps = c.timing.rps(0.001)

Return fractional number of requests that could be performed in one second if
every singe one took the given amount of time in seconds or ``None`` if the
number is too low. ::

    # Log more timing information
    c.timing.begin('web_stuff')
    ...
    elapsed = c.timing.elapsed('web_stuff')
    rps = c.timing.rps(elapsed)
    c.app.log.debug(f'Web stuff took {elapsed} seconds ({rps} per second)')

timing.server_timing ::

    c.timing.server_timing('metric')
    c.timing.server_timing('metric', 'Some Description')
    c.timing.server_timing('metric', 'Some Description', 0.001)

Create ``Server-Timing`` header with optional description and duration. ::

    # "Server-Timing: miss"
    c.timing.server_timing('miss')

    # "Server-Timing: dc;desc=atl"
    c.timing.server_timing('dc', 'atl')

    # "Server-Timing: db;desc=Database;dur=0.0001"
    c.timing.begin('database_stuff')
    ...
    elapsed = c.timing.elapsed('database_stuff')
    c.timing.server_timing('db', 'Database', elapsed)

    # "Server-Timing: miss, dc;desc=atl"
    c.timing.server_timing('miss')
    c.timing.server_timing('dc', 'atl')

title ::

    %= title()
    % title('Welcome!')
    % title('Welcome!', foo='bar')

Get or set ``title`` stash value, all additional keyword arguments get merged
into the ``stash``.

ua ::

    %= ua().get('mojolicious.org').result.dom.at('title').text

Alias for :attr:`Pyjoyment.Pyjoyment_App.ua`.

url_for ::

    %= url_for('named', foo='bar', baz='yada')

Alias for :meth:`Pyjoyment.Controller.Pyjoyment_Controller.url_for`. ::

    %= url_for('/index.html').set(query={'foo': 'bar'})

url_with ::

    %= url_with('named', foo='bar', baz='yada')

Does the same as ``url_for``, but inherits query parameters from the current
request. ::

    %= url_with().set(query={'page': 2})

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Plugin::DefaultHelpers
<https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Plugin/DefaultHelpers.pm>`_ of Mojolicious 9.49.
"""

# TODO: the helpers is_fresh, reply.asset, reply.file, reply.static, url_for_asset and url_for_file, when
# Pyjoyment.Static is ported, and validation, when Pyjoyment.Validator is ported
# TODO: the helpers proxy.get_p, proxy.post_p and proxy.start_p, with proxy_app.t, when Pyjo.Test.Pyjo is ported

import Pyjo.Collection
import Pyjo.Exception
import Pyjo.IOLoop
import Pyjo.String.Bytes
import Pyjo.String.HTML
import Pyjo.String.Unicode
import Pyjoyment.Plugin

from Pyjo.Util import dumper, random_bytes

import functools
import time

from collections.abc import Callable
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import Pyjoyment
    import Pyjoyment.Controller

    type Controller = Pyjoyment.Controller.object


class Pyjoyment_Plugin_DefaultHelpers(Pyjoyment.Plugin.object):
    """
    :mod:`Pyjoyment.Plugin.DefaultHelpers` inherits all methods from
    :mod:`Pyjoyment.Plugin` and implements the following new ones.
    """

    def register(self, app: 'Pyjoyment.object', conf: dict[str, Any] | None = None) -> None:
        """::

            plugin.register(Pyjoyment.new())

        Register helpers in :mod:`Pyjoyment` application.
        """
        # Controller alias helpers
        app.helper('app', _app)
        for name in ('param', 'stash', 'session', 'url_for'):
            app.helper(name, _alias(name))

        # Stash key shortcuts (should not generate log messages)
        for name in ('extends', 'layout', 'title'):
            app.helper(name, _stash_key(name))

        app.helper('accepts', _accepts)
        app.helper('b', _b)
        # Not in Mojolicious: u, as Pyjo.String.Unicode is the Mojo::ByteStream of characters
        app.helper('u', _u)
        app.helper('c', _c)
        app.helper('config', _config)

        app.helper('content', functools.partial(_content, False, False))
        app.helper('content_for', functools.partial(_content, True, False))
        app.helper('content_with', functools.partial(_content, False, True))

        app.helper('csrf_token', _csrf_token)
        app.helper('current_route', _current_route)
        app.helper('exception_format', _exception_format)
        app.helper('flash', _flash)
        app.helper('inactivity_timeout', _inactivity_timeout)
        app.helper('redirect_to', _redirect_to)
        app.helper('respond_to', _respond_to)
        app.helper('url_with', _url_with)

        app.helper('dumper', _dumper)
        app.helper('include', _include)

        app.helper('log', _log)

        app.helper('reply.exception', _exception)
        app.helper('reply.not_found', _not_found)
        app.helper('reply.http_exception', _http_exception)
        app.helper('reply.http_not_found', _http_not_found)
        app.helper('reply.html_exception', functools.partial(_development, 'exception'))
        app.helper('reply.html_not_found', functools.partial(_development, 'not_found'))
        app.helper('reply.json_exception', _json_exception)
        app.helper('reply.json_not_found', _json_not_found)
        app.helper('reply.txt_exception', _txt_exception)
        app.helper('reply.txt_not_found', _txt_not_found)

        app.helper('timing.begin', _timing_begin)
        app.helper('timing.elapsed', _timing_elapsed)
        app.helper('timing.rps', _timing_rps)
        app.helper('timing.server_timing', _timing_server_timing)

        app.helper('ua', _ua)


def _accepts(c: 'Controller', *formats: str) -> Any:
    return c.app.renderer.accepts(c, *formats)


def _alias(name: str) -> Callable[..., Any]:
    def helper(c: 'Controller', *args: Any, **values: Any) -> Any:
        return getattr(c, name)(*args, **values)

    return helper


def _app(c: 'Controller') -> 'Pyjoyment.object':
    return c.app


def _b(c: 'Controller', *args: Any) -> Pyjo.String.Bytes.object:
    return Pyjo.String.Bytes.new(*args)


def _block(content: Any) -> Any:
    return content() if callable(content) else content


def _c(c: 'Controller', *args: Any) -> Pyjo.Collection.object[Any]:
    return Pyjo.Collection.new(*args)


def _config(c: 'Controller', *args: Any, **values: Any) -> Any:
    return c.app.config(*args, **values)


def _content(append: bool, replace: bool, c: 'Controller', name: str | None = None, content: Any = None) -> Any:
    name = name or 'content'

    hash = c.stash().setdefault('mojo.content', {})
    if content is not None:
        if append:
            hash[name] = (hash.get(name) or '') + _block(content)
        if replace:
            hash[name] = _block(content)
        elif hash.get(name) is None:
            hash[name] = _block(content)

    content = hash.get(name)
    return Pyjo.String.HTML.new(content if content is not None else '')


def _convert_to_exception(e: Any) -> Pyjo.Exception.object:
    return e if isinstance(e, Pyjo.Exception.object) else Pyjo.Exception.new(e)


def _csrf_token(c: 'Controller') -> str:
    # Generate token and store it in the session
    session = c.session()
    if not session.get('csrf_token'):
        session['csrf_token'] = random_bytes(20).hex()

    # Mask token to protect against BREACH attacks
    mask = random_bytes(20)
    return mask.hex() + bytes(a ^ b for a, b in zip(mask, bytes.fromhex(session['csrf_token']), strict=False)).hex()


def _current_route(c: 'Controller', *args: str) -> Any:
    if (route := c.match.endpoint) is None:
        return ''
    return route.name == args[0] if args else route.name


def _development(page: str, c: 'Controller', e: Any = None) -> 'Controller':
    if page == 'exception':
        c.helpers.log().error((e := _convert_to_exception(e)).inspect())

    # Filtered stash snapshot
    stash = c.stash()
    stash['snapshot'] = {
        key: 'DUMMY' if key == 'app' else value
        for key, value in stash.items()
        if not key.startswith('mojo.') and value is not None
    }
    stash['exception'] = e if page == 'exception' else None

    # Render with fallbacks
    app = c.app
    mode = app.mode
    options = {
        'format': stash.get('format') or app.renderer.default_format,
        'handler': None,
        'status': 500 if page == 'exception' else 404,
        'template': f'{page}.{mode}',
    }
    bundled = 'mojo/' + ('debug' if mode == 'development' else page)
    if _fallbacks(c, options, page, bundled):
        return c
    _fallbacks(c, {**options, 'format': 'html'}, page, bundled)
    return c


def _dumper(c: 'Controller', *values: Any) -> str:
    return dumper(*values)


def _exception(c: 'Controller', e: Any) -> Any:
    return c.helpers.reply.http_exception(e)


def _exception_format(c: 'Controller', *args: str) -> Any:
    stash = c.stash()
    if not stash.get('mojo.exception_format'):
        stash['mojo.exception_format'] = c.app.exception_format
    if not args:
        return stash['mojo.exception_format']
    stash['mojo.exception_format'] = args[0]
    return c


def _fallbacks(c: 'Controller', options: dict[str, Any], template: str, bundled: str) -> bool:
    # Mode specific template
    if c.render_maybe(**options):
        return True

    # Normal template
    if c.render_maybe(**{**options, 'template': template}):
        return True

    # Inline template
    stash = c.stash()
    if options['format'] != 'html':
        return False
    stash.pop('extends', None)
    stash.pop('layout', None)
    return bool(c.render_maybe(bundled, **{**options, 'handler': 'ep'}))


def _flash(c: 'Controller', *args: Any, **values: Any) -> Any:
    # Check old flash
    session = c.session()
    if len(args) == 1 and not isinstance(args[0], dict) and not values:
        return flash.get(args[0]) if (flash := session.get('flash')) is not None else None

    # Initialize new flash and merge values
    new_flash = session.setdefault('new_flash', {})
    for arg in args:
        new_flash.update(arg)
    new_flash.update(values)

    return c


def _http_exception(c: 'Controller', e: Any) -> Any:
    format = c.exception_format()
    if format == 'txt':
        return c.helpers.reply.txt_exception(e)
    if format == 'json':
        return c.helpers.reply.json_exception(e)
    return c.helpers.reply.html_exception(e)


def _http_not_found(c: 'Controller') -> Any:
    format = c.exception_format()
    if format == 'txt':
        return c.helpers.reply.txt_not_found()
    if format == 'json':
        return c.helpers.reply.json_not_found()
    return c.helpers.reply.html_not_found()


def _inactivity_timeout(c: 'Controller', timeout: float) -> 'Controller':
    tx: Any = c.tx
    if stream := Pyjo.IOLoop.stream(tx.connection or ''):
        stream.timeout = timeout
    return c


def _include(c: 'Controller', *args: Any, **values: Any) -> Any:
    return c.render_to_string(*args, **values)


def _json_exception(c: 'Controller', e: Any) -> Any:
    c.stash()['exception'] = _convert_to_exception(e)
    if c.app.mode == 'development':
        return c.render(json={'error': e}, status=500)
    return c.render(json={'error': 'Internal Server Error'}, status=500)


def _json_not_found(c: 'Controller') -> Any:
    return c.render(json={'error': 'Not Found'}, status=404)


def _log(c: 'Controller') -> Any:
    stash = c.stash()
    if not stash.get('mojo.log'):
        stash['mojo.log'] = c.app.log.context(f'[{c.req.request_id}]')
    return stash['mojo.log']


def _not_found(c: 'Controller') -> Any:
    return c.helpers.reply.http_not_found()


def _redirect_to(c: 'Controller', *args: Any, **values: Any) -> 'Controller':
    # Don't override 3xx status
    res = c.res
    res.headers.location = c.url_for(*args, **values).to_str()
    return c.rendered(None if res.is_redirect else 302)


def _respond_to(c: 'Controller', *args: dict[str, Any], **values: Any) -> 'Controller':
    targets = args[0] if args else values

    # Find target
    target = None
    renderer = c.app.renderer
    formats: list[str] = renderer.accepts(c) or []  # pyright: ignore[reportAssignmentType]
    for format in formats or [renderer.default_format]:
        if not (target := targets.get(format)):
            continue
        c.stash()['format'] = format
        break

    # Fallback
    if not target:
        if not (target := targets.get('any')):
            return c.rendered(204)
        c.stash().pop('format', None)

    # Dispatch
    if callable(target):
        target(c)
    else:
        c.render(**target)

    return c


def _timing_begin(c: 'Controller', name: str) -> None:
    c.stash().setdefault('mojo.timing', {})[name] = time.time()


def _timing_elapsed(c: 'Controller', name: str) -> float | None:
    if (started := c.stash().get('mojo.timing', {}).get(name)) is None:
        return None
    return time.time() - started


def _timing_rps(c: 'Controller', elapsed: float | str) -> str | None:
    return None if float(elapsed) == 0 else f'{1 / float(elapsed):.3f}'


def _timing_server_timing(c: 'Controller', metric: str, desc: str | None = None, dur: Any = None) -> None:
    value = metric
    if desc is not None:
        value += f';desc="{desc}"'
    if dur is not None:
        value += f';dur={dur}'
    c.res.headers.append('Server-Timing', value)


def _txt_exception(c: 'Controller', e: Any) -> Any:
    c.stash()['exception'] = _convert_to_exception(e)
    if c.app.mode == 'development':
        return c.render(text=str(e), format='txt', status=500)
    return c.render(text='Internal Server Error', format='txt', status=500)


def _txt_not_found(c: 'Controller') -> Any:
    return c.render(text='Not Found', format='txt', status=404)


def _stash_key(name: str) -> Callable[..., Any]:
    def helper(c: 'Controller', *args: Any, **values: Any) -> Any:
        if not args and not values:
            return c.stash(name)
        return c.stash({name: args[0]} if args else {}, **values)

    return helper


def _url_with(c: 'Controller', *args: Any, **values: Any) -> Any:
    url = c.url_for(*args, **values)
    url.query = c.req.url.query.clone()
    return url


def _u(c: 'Controller', *args: Any) -> Pyjo.String.Unicode.object:
    return Pyjo.String.Unicode.new(*args)


def _ua(c: 'Controller') -> Any:
    return c.app.ua


new = Pyjoyment_Plugin_DefaultHelpers.new
object = Pyjoyment_Plugin_DefaultHelpers
