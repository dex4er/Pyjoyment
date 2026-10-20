"""
Pyjoyment.Renderer - Generate dynamic content
=============================================
::

    from Pyjoyment.Renderer import Renderer

    renderer = Renderer()
    renderer.classes.append('MyApp.Controller.Foo')
    renderer.paths.append('/home/sri/templates')

    import Pyjoyment.Renderer

    renderer = Pyjoyment.Renderer.new()
    renderer.classes.append('MyApp.Controller.Foo')
    renderer.paths.append('/home/sri/templates')

:mod:`Pyjoyment.Renderer` is the standard :mod:`Pyjoyment` renderer.

See also
--------

:mod:`Pyjoyment`, https://mojolicious.org.

Ported from `Mojolicious::Renderer <https://github.com/mojolicious/mojo/blob/v9.49/lib/Mojolicious/Renderer.pm>`_
of Mojolicious 9.49.
"""

import Pyjo.Base
import Pyjo.Cache
import Pyjo.Exception
import Pyjo.File
import Pyjo.Loader

from Pyjo.JSON import encode_json
from Pyjo.String.Template import is_template
from Pyjo.TOML import dump as dump_toml
from Pyjo.Util import decamelize, deprecated, encode, gzip, md5_sum
from Pyjo.YAML import dump

import io
import os
import re
import sys
import weakref

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Self, cast, overload


if TYPE_CHECKING:
    import Pyjoyment.Controller


# A handler gets the renderer, the controller, the file object to write the output to and the options
type Handler = Callable[[Pyjoyment_Renderer, Any, io.StringIO, dict[str, Any]], Any]

# Bundled templates
_TEMPLATES = Pyjo.File.path(__file__).sibling('resources', 'templates')


class Pyjoyment_Renderer(Pyjo.Base.object):
    """
    :mod:`Pyjoyment.Renderer` inherits all methods from :mod:`Pyjo.Base` and
    implements the following new ones.
    """

    def __init__(self) -> None:
        """::

            renderer = Pyjoyment.Renderer.new()

        Construct a new :mod:`Pyjoyment.Renderer` object.
        """
        self.cache: Pyjo.Cache.object[Any, Any] = Pyjo.Cache.new()
        """::

            cache = renderer.cache
            renderer.cache = Pyjo.Cache.new()

        Renderer cache, defaults to a :mod:`Pyjo.Cache` object.
        """

        self.classes = ['__main__']
        """::

            classes = renderer.classes
            renderer.classes = ['__main__']

        Classes to use for finding templates in ``DATA`` sections with
        :mod:`Pyjo.Loader`, first one has the highest precedence, defaults to
        ``__main__``. Only files with exactly two extensions will be used, like
        ``index.html.ep``. Note that for templates to be detected, these
        classes need to have already been loaded and added before
        :meth:`warmup` is called, which usually happens automatically during
        application startup. ::

            # Add another class with templates in DATA section
            renderer.classes.append('Pyjoyment.Plugin.Fun')

            # Add another class with templates in DATA section and higher precedence
            renderer.classes.insert(0, 'Pyjoyment.Plugin.MoreFun')
        """

        self.compress = True
        """::

            boolean = renderer.compress
            renderer.compress = boolean

        Try to negotiate compression for dynamically generated response content
        and ``gzip`` compress it automatically, defaults to true.
        """

        self.default_format = 'html'
        """::

            default = renderer.default_format
            renderer.default_format = 'html'

        The default format to render if ``format`` is not set in the stash,
        defaults to ``html``. Note that changing the default away from ``html``
        is not recommended, as it has the potential to break, for example,
        plugins with bundled templates.
        """

        self.default_handler: str | None = None
        """::

            default = renderer.default_handler
            renderer.default_handler = 'ep'

        The default template handler to use for rendering in cases where
        auto-detection doesn't work, like for ``inline`` templates. An
        ``inline`` template that is a template string of
        :mod:`Pyjo.String.Template` is rendered by the handler ``py`` of
        :mod:`Pyjoyment.Plugin.PyRenderer`.
        """

        self.encoding: str | None = 'UTF-8'
        """::

            encoding = renderer.encoding
            renderer.encoding = 'koi8-r'

        Will encode generated content if set, defaults to ``UTF-8``. Note that
        many renderers also use this value to determine if template files
        should be decoded before processing.
        """

        self.handlers: dict[str, Handler] = {}
        """::

            handlers = renderer.handlers
            renderer.handlers = {'epl': lambda renderer, c, output, options: ...}

        Registered handlers.
        """

        self.helpers: dict[str, Callable[..., Any]] = {}
        """::

            helpers = renderer.helpers
            renderer.helpers = {'url_for': lambda c, *args: ...}

        Registered helpers.
        """

        self.min_compress_size = 860
        """::

            size = renderer.min_compress_size
            renderer.min_compress_size = 1024

        Minimum output size in bytes required for compression to be used if
        enabled, defaults to ``860``.
        """

        self.paths: list[str] = []
        """::

            paths = renderer.paths
            renderer.paths = ['/home/sri/templates']

        Directories to look for templates in, first one has the highest
        precedence. ::

            # Add another "templates" directory
            renderer.paths.append('/home/sri/templates')

            # Add another "templates" directory with higher precedence
            renderer.paths.insert(0, '/home/sri/themes/blue/templates')
        """

        # Not in Mojolicious: the templates of functions, for the handler "py"
        self.templates: dict[str, Callable[..., Any]] = {}
        """::

            templates = renderer.templates
            renderer.templates = {'index.html': lambda c: t('<p>Hello!</p>')}

        Registered templates of functions, by the name of the template with
        its format, as ``index.html``, which the handler ``py`` of
        :mod:`Pyjoyment.Plugin.PyRenderer` renders, before the templates of
        :attr:`paths` and :attr:`classes`.
        """

        self._index: dict[str, str] = {}
        self._namespaces: list[type[Pyjoyment_Renderer_Helpers]] = []
        self._proxy: dict[str, type[Pyjoyment_Renderer_Helpers]] = {}
        self._templates: dict[str, list[str]] | None = None

        # The methods of the proxies go with the renderer, as Mojo removes them in DESTROY
        weakref.finalize(self, _teardown, self._namespaces)

    def accepts(self, c: 'Pyjoyment.Controller.object', *formats: str) -> list[str] | str | None:
        """::

            all = renderer.accepts(Pyjoyment.Controller.new())
            best = renderer.accepts(Pyjoyment.Controller.new(), 'html', 'json')

        Select best possible representation for :mod:`Pyjoyment.Controller`
        object from ``format`` ``GET``/``POST`` parameter, ``format`` stash
        value, or ``Accept`` request header, defaults to returning the first
        extension if no preference could be detected.
        """
        # DEPRECATED!
        req = c.req
        param = req.param('format')
        if param is not None:
            deprecated('The ?format=* parameter is deprecated in favor of ?_format=* for content negotiation')

        # List representations
        fmt = (param if param is not None else req.param('_format')) or c.stash().get('format')
        exts = [fmt] if fmt else []
        exts.extend(c.app.types.detect(req.headers.accept))
        if not formats:
            return exts

        # Find best representation
        for ext in exts:
            if ext in formats:
                return ext
        return None if exts else formats[0]

    def add_handler(self, name: str, cb: Handler) -> Self:
        """::

            renderer = renderer.add_handler('epl', lambda renderer, c, output, options: ...)

        Register a handler. ::

            def foo(renderer, c, output, options):
                ...
                output.write('Hello World!')

            renderer.add_handler('foo', foo)
        """
        self.handlers[name] = cb
        return self

    def add_helper(self, name: str, cb: Callable[..., Any]) -> Self:
        """::

            renderer = renderer.add_helper('url_for', lambda c, *args: ...)

        Register a helper. ::

            def foo(c, *args):
                ...

            renderer.add_helper('foo', foo)
        """
        self.helpers[name] = cb
        self._proxy.clear()
        return self

    @overload
    def add_template[F: Callable[..., Any]](self, name: str, cb: None = None) -> Callable[[F], F]: ...

    @overload
    def add_template(self, name: str, cb: Callable[..., Any]) -> Self: ...

    # Not in Mojolicious: the templates of functions, for the handler "py"
    def add_template(self, name: str, cb: Callable[..., Any] | None = None) -> Any:
        """::

            renderer = renderer.add_template('index.html', lambda c: t('<p>Hello!</p>'))

            @renderer.add_template('index.html')
            def index(c): ...

        Register a template of a function, which gets the controller and
        returns a template string, see :mod:`Pyjoyment.Plugin.PyRenderer`. ::

            def foo(c, name):
                return t('<p>Hello {name}!</p>')

            renderer.add_template('foo.html', foo)
        """
        if cb is None:

            def decorator(cb: Callable[..., Any]) -> Callable[..., Any]:
                self.add_template(name, cb)
                return cb

            return decorator
        self.templates[name] = cb
        if self._templates is not None:
            self.warmup()
        return self

    def get_data_template(self, options: dict[str, Any]) -> str | bytes | None:
        """::

            template = renderer.get_data_template({'template': 'foo/bar', 'format': 'html', 'handler': 'epl'})

        Return a ``DATA`` section template from :attr:`classes` for an options
        dict with ``template``, ``format``, ``variant`` and ``handler`` values,
        or ``None`` if no template could be found, usually used by handlers.
        """
        if not (template := self.template_name(options)):
            return None
        return cast('str | bytes | None', Pyjo.Loader.data_section(self._index.get(template), template))

    def get_helper(self, name: str) -> 'Callable[..., Any] | type[Pyjoyment_Renderer_Helpers] | None':
        """::

            helper = renderer.get_helper('url_for')

        Get a helper by full name, generate a helper dynamically for a prefix,
        or return ``None`` if no helper or prefix could be found. Generated
        helpers return a proxy object containing the current controller object
        and on which nested helpers can be called.
        """
        if h := self._proxy.get(name) or self.helpers.get(name):
            return h

        # The proxy of a prefix is a class with the nested helpers, as Mojo makes it, a helper as a method and a prefix
        # as a property
        found = False
        attrs: dict[str, Any] = {}
        regex = re.compile(rf'^({re.escape(name)}\.([^.]+))' if name else r'^(([^.]+))')
        for key in list(self.helpers):
            if not (m := regex.match(key)):
                continue
            found = True
            sub = self.get_helper(m[1])
            attrs[m[2]] = _attribute(sub)

        if not found:
            return None
        md5 = md5_sum(f'{name}:{id(self)}'.encode())
        cls = type(f'Pyjoyment_Renderer_Helpers_{md5}', (Pyjoyment_Renderer_Helpers,), attrs)
        self._namespaces.append(cls)
        self._proxy[name] = cls
        return cls

    def render(self, c: 'Pyjoyment.Controller.object') -> tuple[str | bytes, str | None] | None:
        """::

            output, format = renderer.render(Pyjoyment.Controller.new())

        Render output through one of the renderers. See
        :meth:`Pyjoyment.Controller.Pyjoyment_Controller.render` for a more
        user-friendly interface.
        """
        stash = c.stash()
        options: dict[str, Any] = {
            'encoding': self.encoding,
            'handler': stash.get('handler'),
            'template': stash.pop('template', None),
            'variant': stash.get('variant'),
        }
        inline = options['inline'] = stash.pop('inline', None)
        if inline is not None and options['handler'] is None:
            # Not in Mojolicious: an inline template string, which the handler "py" renders
            options['handler'] = 'py' if is_template(inline) else self.default_handler
        options['format'] = stash.get('format') or self.default_format

        # Data
        if stash.get('data') is not None:
            return stash.pop('data'), options['format']

        # Text, which is a string as Perl stringifies a number or an object
        if stash.get('text') is not None:
            text = stash.pop('text')
            return _maybe(options.get('encoding'), text if isinstance(text, str) else str(text)), options['format']

        # JSON
        if 'json' in stash:
            return encode_json(stash.pop('json')), 'json'

        # Not in Mojolicious: YAML, in the style of the documents that tools write, as index.yaml of a chart repository
        # of Helm: the items of a sequence at the column of its key, no anchors, and the quotes of YAML 1.1
        if 'yaml' in stash:
            return encode('UTF-8', dump(stash.pop('yaml'), indent_sequences=False, anchors=False)), 'yaml'

        # Not in Mojolicious: TOML, of a table
        if 'toml' in stash:
            return encode('UTF-8', dump_toml(stash.pop('toml'))), 'toml'

        # Template or templateless handler
        if options['template'] is None:
            options['template'] = self.template_for(c)
        if (output := self._render_template(c, options)) is None:
            return None

        # Inheritance
        content = stash.setdefault('mojo.content', {})
        saved = _MISSING
        if local := bool(stash.get('extends') or stash.get('layout')):
            saved = content.get('content', _MISSING)
            content['content'] = output if _visible(output) else None
        try:
            while (next := _next(stash)) and inline is None:
                options['handler'], options['template'] = stash.get('handler'), next
                options['format'] = stash.get('format') or self.default_format
                if (tmp := self._render_template(c, options)) is not None:
                    output = tmp
                if content.get('content') is None and _visible(output):
                    content['content'] = output

            if stash.get('mojo.string'):
                return output, None
            return _maybe(options.get('encoding'), output), options['format']

        finally:
            if local and saved is _MISSING:
                content.pop('content', None)
            elif local:
                content['content'] = saved

    def respond(
        self, c: 'Pyjoyment.Controller.object', output: str | bytes, format: str | None, status: int | str | None = None
    ) -> bool:
        """::

            boolean = renderer.respond(Pyjoyment.Controller.new(), output, format)
            boolean = renderer.respond(Pyjoyment.Controller.new(), output, format, status)

        Finalize dynamically generated response content and :attr:`compress`
        it if possible.
        """
        stash = c.stash()
        respond = stash.get('mojo.respond')
        stash['mojo.respond'] = (respond or 0) + 1
        if respond:
            raise Pyjo.Exception.new('A response has already been rendered')

        # Gzip compression
        res = c.res
        if self.compress and len(output) >= self.min_compress_size:
            headers = res.headers
            headers.append('Vary', 'Accept-Encoding')
            accept = re.search(r'gzip', c.req.headers.accept_encoding or '', re.IGNORECASE)
            if accept and not headers.content_encoding:
                headers.content_encoding = 'gzip'
                output = gzip(output if isinstance(output, bytes) else output.encode())

        res.body = output if isinstance(output, bytes) else output.encode()
        c.app.types.content_type(c, ext=format)
        return bool(c.rendered(status))

    def template_for(self, c: 'Pyjoyment.Controller.object') -> str | None:
        """::

            name = renderer.template_for(Pyjoyment.Controller.new())

        Return default template name for :mod:`Pyjoyment.Controller` object, or
        ``None`` if no name could be generated.
        """
        # Normal default template
        stash = c.stash()
        controller, action = stash.get('controller'), stash.get('action')
        if controller and action:
            return '/'.join([*decamelize(controller.replace('.', '::')).split('-'), action])

        # Try the route name if we don't have controller and action
        if (route := c.match.endpoint) is None:
            return None
        return route.name

    def template_handler(self, options: dict[str, Any]) -> str | None:
        """::

            handler = renderer.template_handler({'template': 'foo/bar', 'format': 'html'})

        Return handler for an options dict with ``template``, ``format`` and
        ``variant`` values, or ``None`` if no handler could be found.
        """
        if not (file := self.template_name(options)):
            return None
        if not (handlers := (self._templates or {}).get(file)):
            return self.default_handler
        return handlers[0]

    def template_name(self, options: dict[str, Any]) -> str | None:
        """::

            template = renderer.template_name({'template': 'foo/bar', 'format': 'html', 'handler': 'epl'})

        Return a template name for an options dict with ``template``,
        ``format``, ``variant`` and ``handler`` values, or ``None`` if no
        template could be found, usually used by handlers.
        """
        if (template := options.get('template')) is None:
            return None
        if not (format := options.get('format')):
            return None
        template = f'{template}.{format}'

        if self._templates is None:
            self.warmup()
        templates = self._templates or {}

        # Variants
        handler = options.get('handler')
        if (variant := options.get('variant')) is not None:
            variant = f'{template}+{variant}'
            handlers = templates.get(variant, [])
            if (handlers and handler is None) or handler in handlers:
                template = variant

        return f'{template}.{handler}' if handler is not None else template

    def template_path(self, options: dict[str, Any]) -> str | None:
        """::

            path = renderer.template_path({'template': 'foo/bar', 'format': 'html', 'handler': 'epl'})

        Return the full template path for an options dict with ``template``,
        ``format``, ``variant`` and ``handler`` values, or ``None`` if the file
        does not exist in :attr:`paths`, usually used by handlers.
        """
        if not (name := self.template_name(options)):
            return None
        parts = name.split('/')
        for path in [*self.paths, _TEMPLATES]:
            if os.access(file := Pyjo.File.path(path, *parts).to_str(), os.R_OK):
                return file
        return None

    def warmup(self) -> None:
        """::

            renderer.warmup()

        Prepare templates from :attr:`classes` and :attr:`templates` for
        future use.
        """
        index: dict[str, str] = {}
        templates: dict[str, list[str]] = {}
        self._index, self._templates = index, templates

        # Handlers for templates
        for path in [*self.paths, _TEMPLATES]:
            for file in Pyjo.File.path(path).list_tree():
                name = '/'.join(file.to_rel(path).to_list())
                if m := re.search(r'\.(\w+)$', name):
                    templates.setdefault(name[: m.start()], []).append(m[1])

        # Handlers and classes for DATA templates
        for cls in reversed(self.classes):
            keys = sorted(cast(dict[str, Any], Pyjo.Loader.data_section(cls) or {}))
            for key in keys:
                index[key] = cls
            for key in reversed(keys):
                if m := re.search(r'\.(\w+)$', key):
                    templates.setdefault(key[: m.start()], []).insert(0, m[1])

        # Not in Mojolicious: the handler of the templates of functions
        for key in self.templates:
            templates.setdefault(key, []).insert(0, 'py')

    def _render_template(self, c: 'Pyjoyment.Controller.object', options: dict[str, Any]) -> str | bytes | None:
        if not options.get('handler'):
            options['handler'] = self.template_handler(options)
        if not (handler := options['handler']):
            return None
        if (renderer := self.handlers.get(handler)) is None:
            c.helpers.log().error(f'No handler for "{handler}" found')
            return None

        output = _Output()
        renderer(self, c, output, options)
        return output.value() if output.defined else None


class Pyjoyment_Renderer_Helpers:
    """
    The proxy object of :meth:`Pyjoyment_Renderer.get_helper`, which contains
    the current controller object and on which nested helpers can be called.
    """

    def __init__(self, c: Any) -> None:
        self._c = c

    def __getattr__(self, name: str) -> Any:
        package = f'{type(self).__module__}.{type(self).__qualname__}'

        # The location of the caller, which croak adds to the message
        caller = sys._getframe(1)  # pyright: ignore[reportPrivateUsage]
        at = f'at {caller.f_code.co_filename} line {caller.f_lineno}'
        raise AttributeError(
            f'Can\'t locate object method "{name}" via package "{package}" {at}.\n', name=name, obj=self
        )


# The output of a handler, which tells whether the handler wrote any, as Mojo checks that it is defined, and which
# holds bytes instead of characters for a handler that writes them, as one that removes the encoding of the options
class _Output(io.StringIO):
    defined = False
    data: bytearray | None = None

    def write(self, s: str | bytes, /) -> int:
        self.defined = True
        if isinstance(s, bytes):
            self.data = (self.data or bytearray()) + s
            return len(s)
        return super().write(s)

    def value(self) -> str | bytes:
        return bytes(self.data) if self.data is not None else self.getvalue()


_MISSING: Any = Pyjo.Base.object()


# A nested helper is a method of the proxy, a nested prefix a property that makes its proxy
def _attribute(sub: Any) -> Any:
    if isinstance(sub, type):
        proxy = cast(type[Pyjoyment_Renderer_Helpers], sub)
        return property(lambda helpers: proxy(helpers._c))  # pyright: ignore[reportPrivateUsage]

    def method(helpers: Pyjoyment_Renderer_Helpers, *args: Any, **kwargs: Any) -> Any:
        return sub(helpers._c, *args, **kwargs)  # pyright: ignore[reportPrivateUsage]

    return method


def _maybe(encoding: str | None, output: str | bytes) -> str | bytes:
    return encode(encoding, output) if encoding and isinstance(output, str) else output


# Content that is not only whitespace, of characters or of the bytes of a handler
def _visible(output: str | bytes) -> bool:
    return bool(re.search(rb'\S', output) if isinstance(output, bytes) else re.search(r'\S', output))


def _next(stash: dict[str, Any]) -> str | None:
    if stash.get('extends'):
        return stash.pop('extends')
    if not (layout := stash.pop('layout', None)):
        return None
    return f'layouts/{layout}'


def _teardown(namespaces: list[type[Pyjoyment_Renderer_Helpers]]) -> None:
    for cls in namespaces:
        for name in [name for name in vars(cls) if not name.startswith('__')]:
            delattr(cls, name)


new = Pyjoyment_Renderer.new
object = Pyjoyment_Renderer
Renderer = Pyjoyment_Renderer
