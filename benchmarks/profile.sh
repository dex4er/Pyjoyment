#!/usr/bin/env bash
# profile.sh [-n REQUESTS] [-r REACTOR] [ROOT]: cProfile of Pyjo.Server.Daemon of ROOT (default: the
# working tree) under keep-alive requests on one connection
#
#   PYTHON       CPython for the server and the client (default: python3)
#   PROFILE_OUT  file for the profile (default: daemon.prof in a new temporary directory)
set -u
B=$(cd "$(dirname "$0")" && pwd)
PY=${PYTHON:-python3}
requests=20000
reactor=Asyncio
while getopts n:r: opt; do
  case $opt in
    n) requests=$OPTARG ;;
    r) reactor=$OPTARG ;;
    *) exit 2 ;;
  esac
done
shift $((OPTIND - 1))
root=$(cd "${1:-$B/..}" && pwd)
OUT=${PROFILE_OUT:-$(mktemp -d)/daemon.prof}
port=38460

# python -m puts the current directory first in sys.path, so the server runs in ROOT, or the Pyjo of the
# current directory would be profiled instead
(cd "$root" && PYJO_REACTOR=Pyjo.Reactor.$reactor PYTHONPATH=$root exec "$PY" -m cProfile -o "$OUT" "$B/pyjo_daemon.py" "$port" >/dev/null 2>&1) &
pid=$!
for _ in $(seq 100); do
  curl -s -m 1 -o /dev/null "http://127.0.0.1:$port/" && break
  sleep 0.1
done
WARMUP=0 "$PY" "$B/ka.py" "$port" "$requests"
kill -TERM "$pid"
wait "$pid"

"$PY" - "$OUT" "$requests" <<'EOF'
import pstats
import sys

stats = pstats.Stats(sys.argv[1])
requests = int(sys.argv[2])
print(f'{stats.total_tt:.2f} s, {stats.total_calls / requests:.0f} function calls per request')
stats.sort_stats('tottime').print_stats(25)
EOF
echo "profile: $OUT"
