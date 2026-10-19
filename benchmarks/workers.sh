#!/usr/bin/env bash
# workers.sh [PATTERN...]: the servers of workers, Pyjo.Server.Prefork and Pyjo.Server.Prethread, on a CPython with the
# GIL and on the same CPython free-threaded, and other Python servers with as many workers, on the CPython with the GIL,
# under concurrent requests
#
# Each round runs every scenario, one after the other, so that a change of the load hits all of them, and a scenario
# measures the requests per second of oha for each number of connections, with keep-alive for DURATION seconds and with
# a new connection per request for REQUESTS requests. The end has the medians of the rounds. The scenarios run whose
# names match a pattern of the arguments, as `pyjo*` or `*-ft`, or all of them without arguments.
#
#   PYJO_ROOT    Pyjoyment checkout (default: the one of this script)
#   PYTHON       CPython with the GIL (default: python3)
#   PYTHON_FT    the same CPython, free-threaded (default: python3t)
#   VENV         venv of PYTHON with flask uvicorn uvloop httptools aiohttp tornado gunicorn granian
#                (default: venv next to this script)
#   OHA          the command of oha (default: mise exec oha@1.16.0 -- oha)
#   WORKERS      workers of the servers (default: 4)
#   CONNECTIONS  numbers of connections (default: "1 WORKERS 4*WORKERS")
#   DURATION     seconds of a measurement with keep-alive (default: 10)
#   REQUESTS     requests of a measurement with a new connection per request (default: 5000)
#   ROUNDS       rounds (default: 3)
#   BENCH_OUT    directory for the logs of the servers, the results of oha and results.tsv (default: a new temporary one)
set -u
B=$(cd "$(dirname "$0")" && pwd)
R=${PYJO_ROOT:-$(cd "$B/.." && pwd)}
PY=${PYTHON:-python3}
FT=${PYTHON_FT:-python3t}
V=${VENV:-$B/venv}/bin
read -r -a oha <<<"${OHA:-mise exec oha@1.16.0 -- oha}"
W=${WORKERS:-4}
read -r -a connections <<<"${CONNECTIONS:-1 $W $((4 * W))}"
D=${DURATION:-10}
N=${REQUESTS:-5000}
ROUNDS=${ROUNDS:-3}
OUT=${BENCH_OUT:-$(mktemp -d)}
mkdir -p "$OUT/www" && printf "Your Pyjo is working!" >"$OUT/www/index.html"
echo "logs: $OUT"
"$PY" -VV
"$FT" -VV
"${oha[@]}" --version
echo "workers: $W, connections: ${connections[*]}, reactor: ${PYJO_REACTOR:-detected}"
uptime

# Wait for TIME_WAIT to drain, as a new connection per request uses up the ephemeral ports
drain() { while [[ "$(netstat -an 2>/dev/null | grep -c TIME_WAIT)" -gt 500 ]]; do sleep 5; done; }

stop() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN -t | xargs -r kill
  for _ in $(seq 300); do
    lsof -nP -iTCP:"$1" -sTCP:LISTEN -t >/dev/null || return
    sleep 0.1
  done
  lsof -nP -iTCP:"$1" -sTCP:LISTEN -t | xargs -r kill -9
}

# measure NAME ROUND MODE CONNECTIONS PORT OHA-OPTIONS...: a line of results.tsv
measure() {
  local name=$1 round=$2 mode=$3 c=$4 port=$5 json
  shift 5
  json="$OUT/$name-$round-$mode-$c.json"
  timeout 300 "${oha[@]}" --no-tui --output-format json -c "$c" "$@" "http://127.0.0.1:$port/" >"$json"
  printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$mode" "$c" "$round" \
    "$(yq -p json -o tsv '[.summary.requestsPerSec, .latencyPercentiles.p50 * 1000, .latencyPercentiles.p99 * 1000, .summary.successRate]' "$json")" |
    tee -a "$OUT/results.tsv"
}

# bench NAME PORT ROUND COMMAND...
bench() {
  local name=$1 port=$2 round=$3
  shift 3
  if [[ ${#selected[@]} -gt 0 ]]; then
    local pattern match=
    for pattern in "${selected[@]}"; do
      # shellcheck disable=SC2053 # the argument is a pattern
      [[ $name == $pattern ]] && match=1
    done
    [[ -n $match ]] || return
  fi
  # A server left on the port would share it, as the Pyjo servers listen with SO_REUSEPORT
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN -t >/dev/null; then
    echo "== $name: port $port is busy"
    return
  fi
  drain
  (cd "$B" && exec env PYTHONPATH="$R:$B" PYJO_LOG_LEVEL=info "$@" >>"$OUT/$name.log" 2>&1 &)
  for _ in $(seq 100); do
    curl -s -m 1 -o /dev/null "http://127.0.0.1:$port/" && break
    sleep 0.1
  done
  echo "== $name, round $round: $(curl -s "http://127.0.0.1:$port/")"
  # The workers that the manager spawns after the first one, and the warmup of all of them
  sleep 2
  timeout 300 "${oha[@]}" --no-tui -n 2000 -c "$W" "http://127.0.0.1:$port/" >/dev/null
  for c in "${connections[@]}"; do
    # A server that closes the connection after every response has no keep-alive to measure, and oha would use up the
    # ephemeral ports reconnecting
    if [[ ${KEEPALIVE:-yes} == yes ]]; then
      measure "$name" "$round" keep-alive "$c" "$port" -z "${D}s"
      drain
    fi
    measure "$name" "$round" new-connection "$c" "$port" -n "$N" --disable-keepalive
  done
  stop "$port"
}

selected=("$@")

printf 'scenario\tmode\tconnections\tround\trequests/s\tp50 ms\tp99 ms\tsuccess\n' | tee "$OUT/results.tsv"
for round in $(seq "$ROUNDS"); do
  # Pyjo, Pyjo.HelloWorld
  bench pyjo-prefork 38441 "$round" "$PY" pyjo_workers.py prefork 38441 "$W"
  bench pyjo-prethread 38442 "$round" "$PY" pyjo_workers.py prethread 38442 "$W"
  bench pyjo-prefork-ft 38443 "$round" "$FT" pyjo_workers.py prefork 38443 "$W"
  bench pyjo-prethread-ft 38444 "$round" "$FT" pyjo_workers.py prethread 38444 "$W"

  # Pyjoyment, Pyjoyment.HelloWorld
  bench pyjoyment-prefork 38445 "$round" "$PY" pyjo_workers.py prefork 38445 "$W" pyjoyment
  bench pyjoyment-prethread 38446 "$round" "$PY" pyjo_workers.py prethread 38446 "$W" pyjoyment
  bench pyjoyment-prefork-ft 38447 "$round" "$FT" pyjo_workers.py prefork 38447 "$W" pyjoyment
  bench pyjoyment-prethread-ft 38448 "$round" "$FT" pyjo_workers.py prethread 38448 "$W" pyjoyment

  # The others, with the applications of bench.sh and WORKERS processes, on the CPython with the GIL; gunicorn-threads
  # has WORKERS threads in each of them, http.server and the development server of Flask threads of one process
  bench uvicorn-h11 38451 "$round" "$V/python" -m uvicorn --port 38451 --workers "$W" --loop asyncio --http h11 asgi_app:app
  bench uvicorn-uvloop 38452 "$round" "$V/python" -m uvicorn --port 38452 --workers "$W" --loop uvloop --http httptools asgi_app:app
  bench granian 38453 "$round" "$V/granian" --interface asgi --host 127.0.0.1 --port 38453 --workers "$W" asgi_app:app
  KEEPALIVE=no bench gunicorn 38454 "$round" "$V/gunicorn" -b 127.0.0.1:38454 -w "$W" wsgi_app:app
  bench gunicorn-threads 38459 "$round" "$V/gunicorn" -b 127.0.0.1:38459 -k gthread -w "$W" --threads "$W" wsgi_app:app
  bench aiohttp 38455 "$round" "$V/gunicorn" -b 127.0.0.1:38455 -k aiohttp.GunicornWebWorker -w "$W" aiohttp_app:app
  bench tornado 38456 "$round" "$V/python" tornado_app.py 38456 "$W"
  bench http.server 38457 "$round" "$V/python" -m http.server --bind 127.0.0.1 --protocol HTTP/1.1 -d "$OUT/www" 38457
  KEEPALIVE=no bench flask 38458 "$round" "$V/python" -m flask --app flask_app run --port 38458 --with-threads
done

# The medians of the rounds, in the order of the scenarios
echo
echo "== medians"
perl -F'\t' -lane '
  next if $. == 1;
  my $k = join "\t", @F[0 .. 2];
  push @order, $k unless $rows{$k};
  push @{$rows{$k}}, [@F[4 .. 7]];
  END {
    print join "\t", qw(scenario mode connections requests/s p50_ms p99_ms success);
    for my $k (@order) {
      my @r = @{$rows{$k}};
      my @m = map {
        my $i = $_;
        my @v = sort { $a <=> $b } map { $_->[$i] } @r;
        @v % 2 ? $v[@v / 2] : ($v[@v / 2 - 1] + $v[@v / 2]) / 2;
      } 0 .. 3;
      printf "%s\t%.0f\t%.3f\t%.3f\t%s\n", $k, @m;
    }
  }
' "$OUT/results.tsv" | column -t -s $'\t'
uptime
