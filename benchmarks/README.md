# Benchmarks

Hello world servers measured with one connection and one request at a time:
Pyjoyment on its own servers and through ASGI and WSGI, and other Python
servers next to it. The numbers are the latency of a request, not the
throughput under concurrency, and the cost of the client, which is Python too,
is in them: compare the servers with each other, or one version of Pyjoyment
with another, not with numbers measured elsewhere.

The scripts are a recipe as much as a tool. An agent may copy them to a
scratch directory and adapt them to what it measures, keeping the rules in
[Measuring well](#measuring-well).

## Requirements

- `curl`, `lsof`, `netstat` and `ab` (ApacheBench, part of macOS and of the
  `apache2-utils` package on Debian)
- The Python of `mise.toml`, and PyPy for its scenarios
- A venv with the other servers, next to the scripts:

  ```sh
  uv venv --python "$(mise exec -- which python)" benchmarks/venv
  uv pip install --python benchmarks/venv/bin/python \
    flask uvicorn uvloop httptools aiohttp tornado gunicorn granian
  ```

  `benchmarks/venv` is not tracked; `VENV` points the scripts at another one.

## Scripts

| Script                                         | What it does                                                                                                                                                            |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bench.sh [SCENARIO...]`                       | Every server, or the scenarios named: keep-alive 3 times, a new connection per request, and `ab -c 1`                                                                   |
| `ab.sh [-n PAIRS] [-r REACTOR]... [REF]`       | `Pyjo.Server.Daemon` of a git ref (default `master`) against the working tree, interleaved, with the medians and the gain                                               |
| `profile.sh [-n REQUESTS] [-r REACTOR] [ROOT]` | `cProfile` of `Pyjo.Server.Daemon` under keep-alive requests, with the function calls per request and the top of the profile                                            |
| `ka.py PORT N`                                 | The client: `GET /` on one connection, reads by `Content-Length`; `RECONNECT=1` opens a connection for every request, `WARMUP` sets the requests before the measurement |

The applications answer `Your Pyjo is working!`: `hello.py` and
`pyjo_daemon.py` are `Pyjo.HelloWorld` on `Pyjo.Server.Reload` and
`Pyjo.Server.Daemon`, `pyjo_asgi_app.py` and `pyjo_wsgi_app.py` the same
through `Pyjo.Server.ASGI` and `Pyjo.Server.WSGI`, and the others are the
smallest application of each framework.

```sh
PYTHON=$(mise exec -- which python) PYPY=pypy3 benchmarks/bench.sh
PYTHON=$(mise exec -- which python) benchmarks/bench.sh pyjo-daemon-asyncio pyjo-daemon-poll
PYTHON=$(mise exec -- which python) benchmarks/ab.sh -n 8 -r Asyncio master
PYTHON=$(mise exec -- which python) benchmarks/profile.sh -r Poll
```

## Measuring well

- **A quiet machine.** Other work on the machine, a container runtime above
  all, makes the runs vary by tens of percent and hides a gain of a few. Ask
  for the machine to be freed before measuring, and report the load average
  that the scripts print before and after with the numbers.
- **Interleaved A/B.** A change is measured with `ab.sh`, which runs the two
  versions one after the other, several pairs, so that a change of the load
  hits both; report the medians and whether one side won every pair. A single
  run of each is not a result.
- **Below the noise, count.** A gain of a percent or two does not show in the
  time; the function calls per request of `profile.sh` do, and they do not
  depend on the load.
- **`python -m` puts the current directory first in `sys.path`.** A profile
  run with `python -m cProfile` from one checkout imports the Pyjo of that
  checkout, whatever `PYTHONPATH` says: run it in the directory of the code to
  profile, as `profile.sh` does. A script run by its path has its own
  directory first instead, so `ab.sh` and `bench.sh` run the servers that way.
- **One server per port.** The Pyjo servers listen with `SO_REUSEPORT`, so a
  server left over from an earlier run shares the port and answers part of the
  requests; `bench.sh` skips a busy port, check with
  `lsof -nP -iTCP:PORT -sTCP:LISTEN` otherwise. The process of `$!` after
  `mise exec` is not the server: run the Python of `mise exec -- which python`
  directly.
- **Ephemeral ports.** A new connection per request leaves the ports of the
  client in `TIME_WAIT`, ~16k of them on macOS; `bench.sh` waits for them to
  drain between the scenarios.
- **Nothing left running.** Stop every server the measurement started, and
  check the ports afterwards.

## Known behaviour

- Pyjoyment closes a keep-alive connection after `max_requests` (100), as
  Mojolicious does; `ka.py` opens a new one.
- `ab -k` waits on Pyjoyment, and on Mojolicious alike: to an HTTP/1.0 request
  with `Connection: Keep-Alive` both answer HTTP/1.1 without
  `Connection: keep-alive`, so ab waits for the close until
  `keep_alive_timeout`. `bench.sh` runs `ab` without `-k`.
- The development server of Flask and gunicorn with its sync worker close the
  connection after every response, so they have no keep-alive numbers. The
  server of Flask closes it ~12 ms after the response, which `ab` waits for.
- An ASGI application without `Content-Length` is sent chunked, which `ka.py`
  does not read: the applications set it, as Pyjoyment does.
- The JIT of PyPy needs a warmup: the PyPy scenarios send 20 000 requests
  before measuring.
