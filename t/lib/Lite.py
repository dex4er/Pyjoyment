import Pyjo.IOLoop
import Pyjo.JSON
import Pyjo.Log
import Pyjo.Server
import Pyjo.Transaction.HTTP
import Pyjo.URL
import Pyjo.UserAgent.Server

import os
import re
import sys
import weakref


# A minimal Mojolicious::Lite for the tests that Mojo writes on it: an application with routes for HTTP and WebSocket,
# hooks, a user agent and a controller that renders text, data and JSON, writes and finishes, with what the servers need
# from an application
# TODO: Pyjoyment.Lite in its place, when it is ported


class Controller:
    def __init__(self, app, tx, stash):
        self.app = app
        self.tx = tx
        self.stash = stash
        self.is_rendered = False

    @property
    def req(self):
        return self.tx.req

    @property
    def res(self):
        return self.tx.res

    def finish(self, *args):
        tx = self.tx

        # WebSocket
        if tx.is_websocket:
            tx.finish(*args)
            return self if tx.established else self.rendered(101)

        # Chunked stream
        if tx.res.content.is_chunked:
            return self.write_chunk(*args).write_chunk(b'') if args else self.write_chunk(b'')

        # Normal stream
        return self.write(*args).write(b'') if args else self.write(b'')

    def inactivity_timeout(self, timeout):
        if (stream := Pyjo.IOLoop.stream(self.tx.connection)) is not None:
            stream.timeout = float(timeout)
        return self

    def on(self, name, cb):
        tx = self.tx
        if tx.is_websocket and not tx.established:
            self.rendered(101)
        return tx.on(name, lambda tx, *args: cb(self, *args))

    def param(self, name):
        if name in self.stash:
            return self.stash[name]
        return self.req.param(name)

    def send(self, msg, cb=None):
        tx = self.tx
        tx.send(msg, (lambda tx, *args: cb(self, *args)) if cb else None)
        return self if tx.established else self.rendered(101)

    def url_for(self, path='/'):
        url = Pyjo.URL.new(path)
        url.base = self.req.url.base.clone()
        return url

    def write(self, chunk=None, cb=None):
        if chunk is not None and not isinstance(chunk, bytes):
            chunk = str(chunk).encode()
        self.res.content.write(chunk, (lambda content, *args: cb(self)) if cb else None)
        return self.rendered()

    def redirect_to(self, path):
        res = self.res
        res.headers.location = str(self.url_for(path).to_abs())
        return self.rendered(None if res.is_redirect else 302)

    def render(self, *, data=None, json=None, status=None, text=None, **stash):
        res = self.res
        if json is not None:
            res.headers.content_type = 'application/json;charset=UTF-8'
            res.body = Pyjo.JSON.encode_json(json)
        elif data is not None:
            res.headers.content_type = 'text/html;charset=UTF-8'
            res.body = data if isinstance(data, bytes) else str(data).encode()
        else:
            res.headers.content_type = 'text/html;charset=UTF-8'
            res.body = str(text if text is not None else '').encode()
        return self.rendered(status)

    def rendered(self, status=None):
        res = self.res
        if status or not res.code:
            res.code = status or 200
        self.is_rendered = True
        self.tx.resume()
        return self

    def write_chunk(self, chunk, cb=None):
        chunk = chunk if isinstance(chunk, bytes) else str(chunk).encode()
        self.res.content.write_chunk(chunk, (lambda content, *args: cb(self)) if cb else None)
        return self.rendered()


class Routes:
    def __init__(self):
        self.routes = []

    def any(self, pattern, *args):
        return self._route(None, pattern, args)

    def delete(self, pattern, *args):
        return self._route(['DELETE'], pattern, args)

    def get(self, pattern, *args):
        return self._route(['GET', 'HEAD'], pattern, args)

    def options(self, pattern, *args):
        return self._route(['OPTIONS'], pattern, args)

    def patch(self, pattern, *args):
        return self._route(['PATCH'], pattern, args)

    def post(self, pattern, *args):
        return self._route(['POST'], pattern, args)

    def put(self, pattern, *args):
        return self._route(['PUT'], pattern, args)

    def websocket(self, pattern, *args):
        return self._route(['WEBSOCKET'], pattern, args)

    def match(self, tx):
        method, path = tx.req.method.upper(), tx.req.url.path.to_route()
        for methods, regex, defaults, cb in self.routes:
            # WebSocket routes match only WebSocket handshakes
            if methods == ['WEBSOCKET']:
                if not tx.is_websocket:
                    continue
            elif methods is not None and method not in methods:
                continue
            if m := regex.fullmatch(path):
                return {**defaults, **{k: v for k, v in m.groupdict().items() if v is not None}}, cb
        return None

    def _route(self, methods, pattern, args):
        defaults = next((arg for arg in args if isinstance(arg, dict)), {})
        cb = next((arg for arg in args if callable(arg)), None)

        # Placeholders ":name" and wildcards "*name"
        regex = re.sub(r'\\\*(\w+)', r'(?P<\1>.*)', re.escape(pattern))
        regex = re.sub(r'\\:(\w+)', r'(?P<\1>[^/.]+)', regex)
        route = (methods, re.compile(regex), defaults, cb)

        # A decorator without the callback
        if cb is None and not defaults:

            def decorator(cb):
                self.routes.append((methods, route[1], defaults, cb))
                return cb

            return decorator
        self.routes.append(route)
        return self


class Mojolicious:
    def __init__(self, **kwargs):
        kwargs |= Pyjo.Server.args_override
        self.log = kwargs.get('log') or Pyjo.Log.new()
        self.mode = kwargs.get('mode') or os.environ.get('PYJO_MODE') or 'development'
        self.moniker = kwargs.get('moniker', 'mojolicious')
        self.routes = Routes()
        self._config = {}
        self._hooks = {}
        self._ua = None

    def build_tx(self):
        return Pyjo.Transaction.HTTP.new()

    def config(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], str) and not kwargs:
            return self._config.get(args[0])
        if not args and not kwargs:
            return self._config
        for arg in args:
            self._config.update(arg)
        self._config.update(kwargs)
        return self

    def handler(self, tx):
        c = Controller(self, tx, {})
        try:
            if (match := self.routes.match(tx)) is None:
                return c.render(text='Page not found', status=404)
            stash, cb = match
            c.stash.update(stash)
            if cb is None:
                return c.render(**{k: v for k, v in stash.items() if k in ('data', 'json', 'status', 'text')})
            # An action that renders nothing leaves the response for later, as the route was found
            cb(c)
        except Exception as e:
            self.log.error(str(e))
            c.render(text='Internal Server Error', status=500)

    def hook(self, name, cb):
        self._hooks.setdefault(name, []).append(cb)
        return self

    def server(self, server):
        for cb in self._hooks.get('before_server_start', []):
            cb(server, self)

    def start(self, *args):
        # Application loader
        if os.environ.get('PYJO_APP_LOADER') is not None:
            Pyjo.Server.loaded_app = self
        return self

    @property
    def ua(self):
        if self._ua is None:
            import Pyjo.UserAgent

            self._ua = Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton)
            self._ua.server.app = weakref.proxy(self)
        return self._ua


class Lite(Mojolicious):
    pass


# The application of the script, as Mojolicious::Lite makes it for the package that uses it, shared by the scripts that
# import it, as Python imports a module once
app = Lite(moniker=os.path.splitext(os.path.basename(sys.argv[0] if sys.argv else ''))[0] or 'mojolicious')


# The default application of the servers of user agents, as Mojolicious::Lite makes it
if Pyjo.UserAgent.Server.app() is None:
    Pyjo.UserAgent.Server.app(app)


def any(pattern, *args):
    return app.routes.any(pattern, *args)


def delete(pattern, *args):
    return app.routes.delete(pattern, *args)


def get(pattern, *args):
    return app.routes.get(pattern, *args)


def options(pattern, *args):
    return app.routes.options(pattern, *args)


def patch(pattern, *args):
    return app.routes.patch(pattern, *args)


def post(pattern, *args):
    return app.routes.post(pattern, *args)


def put(pattern, *args):
    return app.routes.put(pattern, *args)


def websocket(pattern, *args):
    return app.routes.websocket(pattern, *args)


if __name__ == '__main__':
    from Pyjo.Test import plan

    plan(skip_all='helper module, not a test')
