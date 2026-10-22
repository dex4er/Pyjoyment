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
| `lambda/`    | an application of `Pyjoyment.Lite` as an event function of AWS Lambda, deployed with OpenTofu          |
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

The event function of `lambda/` runs on AWS Lambda, with a Function URL, which
OpenTofu creates with the credentials and the region of the default chain of
AWS, and with `-var alb=true` behind an Application Load Balancer in the default
VPC too, which costs for each hour it runs. Its test runs it with
`Pyjo.App.Lambda`, or on AWS, with the URLs of the outputs `url` and `alb_url`
in `TEST_LAMBDA_URL` and `TEST_LAMBDA_ALB_URL`:

```sh
tofu -chdir=examples/lambda init
tofu -chdir=examples/lambda apply -var alb=true
TEST_LAMBDA_URL=$(tofu -chdir=examples/lambda output -raw url) \
  TEST_LAMBDA_ALB_URL=$(tofu -chdir=examples/lambda output -raw alb_url) \
  mise exec -- python -m Pyjo.Prove -l t/examples/lambda/app.py
tofu -chdir=examples/lambda destroy
```

The tests in [`t/examples/`](../t/examples), in the same groups, check some of
the scripts, and the documentation shows them on its page of examples.
