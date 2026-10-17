#!/usr/bin/env bash
# bench.sh [SCENARIO...]: hello world servers, one connection, one request at a time
#
# Each scenario: keep-alive 3 times (if the server keeps connections), a new connection per
# request, and ab -c 1 (HTTP/1.0, no keep-alive). Without arguments, all scenarios run.
#
#   PYJO_ROOT  Pyjoyment checkout (default: the one of this script)
#   PYTHON     CPython for Pyjo and the client (default: python3)
#   PYPY       PyPy for the PyPy scenarios (default: pypy3)
#   VENV       venv with flask uvicorn uvloop httptools aiohttp tornado gunicorn granian
#              (default: venv next to this script)
#   BENCH_OUT  directory for the logs of the servers (default: a new temporary one)
set -u
B=$(cd "$(dirname "$0")" && pwd)
R=${PYJO_ROOT:-$(cd "$B/.." && pwd)}
PY=${PYTHON:-python3}
PP=${PYPY:-pypy3}
V=${VENV:-$B/venv}/bin
OUT=${BENCH_OUT:-$(mktemp -d)}
mkdir -p "$OUT/www" && printf 'Your Pyjo is working!' >"$OUT/www/index.html"
echo "logs: $OUT"
uptime

# Wait for TIME_WAIT to drain, as a new connection per request uses up the ephemeral ports
drain() { while [ "$(netstat -an 2>/dev/null | grep -c TIME_WAIT)" -gt 500 ]; do sleep 5; done; }

stop() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN -t | xargs -r kill
  sleep 1
  lsof -nP -iTCP:"$1" -sTCP:LISTEN -t | xargs -r kill -9
}

# bench NAME PORT KEEPALIVE WARMUP COMMAND...
bench() {
  local name=$1 port=$2 ka=$3 warmup=$4
  shift 4
  if [ ${#selected[@]} -gt 0 ] && [[ " ${selected[*]} " != *" $name "* ]]; then return; fi
  # A server left on the port would share it, as the Pyjo servers listen with SO_REUSEPORT
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN -t >/dev/null; then
    echo "== $name: port $port is busy"
    return
  fi
  drain
  (cd "$B" && exec env PYTHONPATH="$R:$B" "$@" >"$OUT/$name.log" 2>&1 &)
  for _ in $(seq 100); do
    curl -s -m 1 -o /dev/null "http://127.0.0.1:$port/" && break
    sleep 0.1
  done
  echo "== $name: $(curl -s "http://127.0.0.1:$port/")"
  if [ "$ka" = yes ]; then
    for _ in 1 2 3; do WARMUP=$warmup timeout 300 "$PY" "$B/ka.py" "$port" 20000 2>&1 | tail -1; done
  fi
  drain
  RECONNECT=1 WARMUP=500 timeout 300 "$PY" "$B/ka.py" "$port" 4000 2>&1 | tail -1
  drain
  timeout 300 ab -q -c 1 -n 5000 "http://127.0.0.1:$port/" 2>&1 | grep -E "Requests per second|Failed requests: +[1-9]" | sed 's/^/ab: /'
  stop "$port"
}

selected=("$@")

# Pyjo
bench pyjo-reload-asyncio 38411 yes 1000 env PYJO_REACTOR=Pyjo.Reactor.Asyncio "$PY" -m Pyjo.Server.Reload -l http://127.0.0.1:38411 -w none hello.py
bench pyjo-reload-poll 38412 yes 1000 env PYJO_REACTOR=Pyjo.Reactor.Poll "$PY" -m Pyjo.Server.Reload -l http://127.0.0.1:38412 -w none hello.py
bench pyjo-daemon-asyncio 38426 yes 1000 env PYJO_REACTOR=Pyjo.Reactor.Asyncio "$PY" pyjo_daemon.py 38426
bench pyjo-daemon-poll 38429 yes 1000 env PYJO_REACTOR=Pyjo.Reactor.Poll "$PY" pyjo_daemon.py 38429
bench pypy-pyjo-daemon-asyncio 38430 yes 20000 env PYJO_REACTOR=Pyjo.Reactor.Asyncio "$PP" pyjo_daemon.py 38430
bench pypy-pyjo-daemon-poll 38427 yes 20000 env PYJO_REACTOR=Pyjo.Reactor.Poll "$PP" pyjo_daemon.py 38427
bench uvicorn-pyjo-asgi 38423 yes 1000 "$V/python" -m uvicorn --port 38423 --loop uvloop --http httptools pyjo_asgi_app:app
bench granian-pyjo-asgi 38425 yes 1000 "$V/granian" --interface asgi --host 127.0.0.1 --port 38425 --workers 1 pyjo_asgi_app:app
bench gunicorn-pyjo-wsgi 38421 no 0 "$V/gunicorn" -w 1 -b 127.0.0.1:38421 pyjo_wsgi_app:app

# The others
bench http.server 38413 yes 1000 "$PY" -m http.server --bind 127.0.0.1 --protocol HTTP/1.1 -d "$OUT/www" 38413
bench pypy-http.server 38428 yes 20000 "$PP" -m http.server --bind 127.0.0.1 --protocol HTTP/1.1 -d "$OUT/www" 38428
bench flask 38414 no 0 "$V/python" -m flask --app flask_app run --port 38414
bench uvicorn-asyncio-h11 38415 yes 1000 "$V/python" -m uvicorn --port 38415 --loop asyncio --http h11 asgi_app:app
bench uvicorn-uvloop-httptools 38416 yes 1000 "$V/python" -m uvicorn --port 38416 --loop uvloop --http httptools asgi_app:app
bench aiohttp 38417 yes 1000 "$V/python" aiohttp_app.py 38417
bench tornado 38422 yes 1000 "$V/python" tornado_app.py 38422
bench granian-asgi 38424 yes 1000 "$V/granian" --interface asgi --host 127.0.0.1 --port 38424 --workers 1 asgi_app:app
bench gunicorn-wsgi 38420 no 0 "$V/gunicorn" -w 1 -b 127.0.0.1:38420 wsgi_app:app

uptime
