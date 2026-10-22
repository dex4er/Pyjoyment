# Examples

Short scripts that show what Pyjoyment does, grouped by the part of it they
use. A script with a `.pl` file next to it is the port of a Mojolicious
script, which shows the same thing in Perl.

## Layout

| Directory    | What it holds                                                                                          |
| ------------ | ------------------------------------------------------------------------------------------------------ |
| `pyjo/`      | the toolkit: objects, events, URLs, the event loop, and TCP clients and servers on it                  |
| `pyjoyment/` | applications of the framework, `Pyjoyment.Lite`                                                        |
| `mount/`     | applications of other frameworks, WSGI, ASGI, FastCGI, CGI and AWS Lambda, mounted in `Pyjoyment.Lite` |
| `servers/`   | applications on the servers of Pyjoyment, on ASGI, WSGI and CGI, and on AWS Lambda                     |
| `ua/`        | the user agent: requests, web scraping, and a server and a user agent in one event loop                |

## Running

Run the scripts from the root of the repository, with the tools of
`mise.toml`, and `PYTHONPATH` set to it, as Pyjoyment is not installed there:

```sh
PYTHONPATH=. mise exec -- python examples/pyjo/url.py
PYTHONPATH=. mise exec -- python examples/ua/get.py https://github.com
```

An application of `Pyjoyment.Lite` takes a command, as `daemon`, which serves
it on <http://localhost:3000>:

```sh
PYTHONPATH=. mise exec -- python examples/pyjoyment/hello.py daemon
```

A script that needs a library which Pyjoyment does not depend on, as the
servers of `hello_world_uvicorn.py` and `hello_world_werkzeug.py` or the
`dnspython` of `resolv_dns.py`, gets it from uv:

```sh
PYTHONPATH=. mise exec -- uv run --no-project --with uvicorn \
  python examples/servers/hello_world_uvicorn.py
```

A script that needs a program which Pyjoyment does not run, as php-fpm for
`mount_fastcgi_php.py`, says how to start it in its comment:

```sh
(cd examples/mount && php-fpm -n -y php/php-fpm.conf -F) &
PYTHONPATH=. mise exec -- python examples/mount/mount_fastcgi_php.py daemon
```

The tests in [`t/examples/`](../t/examples), in the same groups, check some of
the scripts, and the documentation shows them on its page of examples.
