#!/usr/bin/env bash
# ab.sh [-n PAIRS] [-r REACTOR]... [REF]: Pyjo.Server.Daemon of REF (default: master) against the working
# tree, keep-alive on one connection, the two interleaved, so that a change of the load of the machine
# hits both alike
#
#   PYTHON  CPython for the servers and the client (default: python3)
set -u
B=$(cd "$(dirname "$0")" && pwd)
R=$(cd "$B/.." && pwd)
PY=${PYTHON:-python3}
pairs=6
reactors=()
while getopts n:r: opt; do
  case $opt in
    n) pairs=$OPTARG ;;
    r) reactors+=("$OPTARG") ;;
    *) exit 2 ;;
  esac
done
shift $((OPTIND - 1))
ref=${1:-master}
[[ ${#reactors[@]} -gt 0 ]] || reactors=(Asyncio Poll)

W=$(mktemp -d)/ref
git -C "$R" worktree add -q --detach "$W" "$ref" || exit 1
trap 'git -C "$R" worktree remove --force "$W"' EXIT

# run PORT ROOT REACTOR: the requests per second of the Pyjo of ROOT; the script is run by its path, not
# with -m, so that the current directory does not come first in sys.path
run() {
  local port=$1 root=$2 reactor=$3
  PYJO_REACTOR=Pyjo.Reactor.$reactor PYTHONPATH=$root "$PY" "$B/pyjo_daemon.py" "$port" >/dev/null 2>&1 &
  local pid=$!
  for _ in $(seq 100); do
    curl -s -m 1 -o /dev/null "http://127.0.0.1:$port/" && break
    sleep 0.1
  done
  "$PY" "$B/ka.py" "$port" 20000 | awk '{print $2}'
  kill -TERM "$pid"
  wait "$pid"
}

median() { sort -n | awk '{a[NR] = $1} END {print (NR % 2 ? a[(NR + 1) / 2] : int((a[NR / 2] + a[NR / 2 + 1]) / 2))}'; }

uptime
echo "$ref: $(git -C "$W" log --oneline -1)"
echo "tree: $(git -C "$R" log --oneline -1)$(git -C "$R" diff --quiet HEAD || echo ' (with changes)')"
for reactor in "${reactors[@]}"; do
  echo "== $reactor"
  a=() b=()
  for _ in $(seq "$pairs"); do
    x=$(run 38450 "$W" "$reactor")
    y=$(run 38451 "$R" "$reactor")
    a+=("$x") b+=("$y")
    echo "$ref $x  tree $y"
  done
  ma=$(printf '%s\n' "${a[@]}" | median)
  mb=$(printf '%s\n' "${b[@]}" | median)
  echo "median: $ref $ma  tree $mb  ($(LC_ALL=C awk -v a="$ma" -v b="$mb" 'BEGIN {printf "%+.1f%%", (b - a) / a * 100}'))"
done
uptime
