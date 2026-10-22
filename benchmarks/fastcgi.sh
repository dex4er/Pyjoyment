#!/usr/bin/env bash
# fastcgi.sh [-n ROUNDS] [-m MAX] [-r REACTOR]: Pyjo.App.FastCGI with hello.php on php-fpm, over TCP/IP and a UNIX
# domain socket, with a connection for each request and with MAX connections kept (default 4), keep-alive on one
# connection of the client, the scenarios interleaved in rounds, with the medians and the TIME_WAIT sockets that a
# run leaves to php-fpm
#
#   PYTHON   CPython for the server and the client (default: python3)
#   PHP_FPM  php-fpm (default: the one on PATH)
set -u
B=$(cd "$(dirname "$0")" && pwd)
R=$(cd "$B/.." && pwd)
PY=${PYTHON:-python3}
FPM=${PHP_FPM:-$(command -v php-fpm)}
rounds=5
max=4
reactor=Asyncio
while getopts n:m:r: opt; do
  case $opt in
    n) rounds=$OPTARG ;;
    m) max=$OPTARG ;;
    r) reactor=$OPTARG ;;
    *) exit 2 ;;
  esac
done
[[ -x $FPM ]] || {
  echo "php-fpm not found" >&2
  exit 1
}

# php-fpm with a pool on TCP/IP and one on a UNIX domain socket, with workers enough for the connections kept
T=$(mktemp -d)
fpm_port=38460
cat >"$T/php-fpm.conf" <<CONF
[global]
error_log = $T/php-fpm.log
daemonize = no

[tcp]
listen = 127.0.0.1:$fpm_port
pm = static
pm.max_children = $((max + 2))

[unix]
listen = $T/fpm.sock
pm = static
pm.max_children = $((max + 2))
CONF
"$FPM" -n -y "$T/php-fpm.conf" -F &
fpm=$!
trap 'kill -TERM $fpm; wait $fpm; rm -rf "$T"' EXIT
for _ in $(seq 100); do
  [[ -S $T/fpm.sock ]] && break
  sleep 0.1
done

unix="fcgi+unix://$("$PY" -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$T/fpm.sock")"
tcp="fcgi://127.0.0.1:$fpm_port"

# time_wait: the TIME_WAIT sockets of the connections to php-fpm on TCP/IP
time_wait() { netstat -an | grep -cE "127\.0\.0\.1[.:]${fpm_port}[[:space:]].*TIME_WAIT"; }

# run PORT LOCATION: the requests per second, and the TIME_WAIT sockets that the run left
run() {
  local port=$1 location=$2
  PYJO_REACTOR=Pyjo.Reactor.$reactor PYTHONPATH=$R "$PY" "$B/pyjo_fastcgi.py" "$port" "$location" "$B/hello.php" \
    >/dev/null 2>&1 &
  local pid=$!
  for _ in $(seq 100); do
    curl -s -m 1 -o /dev/null "http://127.0.0.1:$port/" && break
    sleep 0.1
  done
  local before
  before=$(time_wait)
  local rate
  rate=$(WARMUP=500 "$PY" "$B/ka.py" "$port" 5000 | awk '{print $2}')
  echo "$rate $(($(time_wait) - before))"
  kill -TERM "$pid"
  wait "$pid"
}

median() { sort -n | awk '{a[NR] = $1} END {print (NR % 2 ? a[(NR + 1) / 2] : int((a[NR / 2] + a[NR / 2 + 1]) / 2))}'; }

scenarios=("tcp 0" "tcp $max" "unix 0" "unix $max")
uptime
echo "tree: $(git -C "$R" log --oneline -1)$(git -C "$R" diff --quiet HEAD || echo ' (with changes)')"
echo "$("$FPM" -v | head -1), $reactor"
for round in $(seq "$rounds"); do
  line="round $round:"
  for scenario in "${scenarios[@]}"; do
    read -r socket connections <<<"$scenario"
    location=$tcp
    [[ $socket == unix ]] && location=$unix
    read -r rate waited <<<"$(run 38461 "$location?max_connections=$connections")"
    echo "$socket $connections $rate $waited" >>"$T/results"
    line+="  $socket/$connections $rate"
  done
  echo "$line"
done
for scenario in "${scenarios[@]}"; do
  read -r socket connections <<<"$scenario"
  rate=$(awk -v s="$socket" -v c="$connections" '$1 == s && $2 == c {print $3}' "$T/results" | median)
  waited=$(awk -v s="$socket" -v c="$connections" '$1 == s && $2 == c {print $4}' "$T/results" | median)
  printf '%-8s max_connections=%-3s %6s req/s  %6s TIME_WAIT\n' "$socket" "$connections" "$rate" "$waited"
done
uptime
