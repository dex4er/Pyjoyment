import Pyjo.IOLoop
import Pyjo.JSON
import Pyjo.Log
import Pyjo.Server
import Pyjo.Transaction.HTTP

import os
import re
import sys


# A minimal Mojolicious::Lite for the tests that Mojo writes on it: an application with routes, hooks and a controller
# that renders text, data and JSON, with what the servers need from an application
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

    def inactivity_timeout(self, timeout):
        if (stream := Pyjo.IOLoop.stream(self.tx.connection)) is not None:
            stream.timeout = timeout
        return self

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
        if status is not None:
            res.code = status
        elif not res.code:
            res.code = 200
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

    def get(self, pattern, *args):
        return self._route(['GET', 'HEAD'], pattern, args)

    def post(self, pattern, *args):
        return self._route(['POST'], pattern, args)

    def match(self, method, path):
        for methods, regex, defaults, cb in self.routes:
            if methods is not None and method.upper() not in methods:
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
            if (match := self.routes.match(tx.req.method, tx.req.url.path.to_route())) is None:
                return c.render(text='Page not found', status=404)
            stash, cb = match
            c.stash.update(stash)
            if cb is None:
                return c.render(**{k: v for k, v in stash.items() if k in ('data', 'json', 'text')})
            cb(c)
            if not c.is_rendered and not tx.res.code:
                c.render(text='Page not found', status=404)
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


class Lite(Mojolicious):
    pass


# The application of the script, as Mojolicious::Lite makes it for the package that uses it, shared by the scripts that
# import it, as Python imports a module once
app = Lite(moniker=os.path.splitext(os.path.basename(sys.argv[0] if sys.argv else ''))[0] or 'mojolicious')


def any(pattern, *args):
    return app.routes.any(pattern, *args)


def get(pattern, *args):
    return app.routes.get(pattern, *args)


def post(pattern, *args):
    return app.routes.post(pattern, *args)


if __name__ == '__main__':
    from Pyjo.Test import plan

    plan(skip_all='helper module, not a test')
