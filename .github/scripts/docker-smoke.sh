#!/usr/bin/env bash
# Smoke test of the image of "generate dockerfile": generates an application,
# builds its image with the wheel of the checkout, runs it, requests its pages
# and stops it, which has to be graceful.
#
# Usage: .github/scripts/docker-smoke.sh app|lite|lite-pep723
#
#   app           generate app, run as python -m MyApp, with --user app
#   lite          generate lite-app, with generate pyproject
#   lite-pep723   generate lite-app, with the inline metadata of PEP 723
#
# It needs docker, python and uv on PATH, as "mise exec --" gives them.

set -euo pipefail

variant=${1:?Usage: $0 app|lite|lite-pep723}
root=$(cd "$(dirname "$0")/../.." && pwd)
work=$(mktemp -d)
name=pyjo-smoke-${variant}

cleanup() {
  status=$?
  if [[ ${status} -ne 0 ]] && docker inspect "${name}" >/dev/null 2>&1; then
    echo "--- logs of ${name}"
    docker logs "${name}" 2>&1 || true
  fi
  docker rm -f "${name}" >/dev/null 2>&1 || true
  docker rmi -f "${name}" >/dev/null 2>&1 || true
  rm -rf "${work}"
  exit "${status}"
}
trap cleanup EXIT

fail() {
  echo "not ok - $*" >&2
  exit 1
}

# The modules of the checkout run the generators
export PYTHONPATH=${root}
unset PYJO_EXE PYJO_HOME

# The wheel of the checkout goes into the image, as the version that is tested
# is not on PyPI
uv build --wheel --quiet --out-dir "${work}/wheel" "${root}"
wheel=$(cd "${work}/wheel" && echo *.whl)
sources="[tool.uv.sources]
Pyjoyment = { path = \"${wheel}\" }"

mkdir "${work}/project"
cd "${work}/project"

case ${variant} in
  app)
    python -m Pyjoyment generate app >/dev/null
    cd my_app
    run=(python -m MyApp)
    options=(--user app)
    pages=(/ /index.html)
    ;;
  lite)
    python -m Pyjoyment generate lite-app >/dev/null
    run=(python myapp.py)
    options=()
    pages=(/)
    "${run[@]}" generate pyproject >/dev/null
    ;;
  lite-pep723)
    python -m Pyjoyment generate lite-app >/dev/null
    run=(python myapp.py)
    options=()
    pages=(/)
    METADATA="# /// script
# requires-python = \">=3.12\"
# dependencies = [\"Pyjoyment\"]
$(echo "${sources}" | perl -pe 's/^/# /')
# ///" perl -0pi -e 's/\A(#!.*\n)/$1$ENV{METADATA}\n/' myapp.py
    ;;
  *)
    fail "unknown variant ${variant}"
    ;;
esac

# Dependencies with the wheel of the checkout, locked
cp "${work}/wheel/${wheel}" .
if [[ -f pyproject.toml ]]; then
  printf '\n%s\n' "${sources}" >>pyproject.toml
  uv lock --quiet
else
  uv lock --quiet --script myapp.py
fi

"${run[@]}" generate dockerfile "${options[@]}" >/dev/null
[[ -f .dockerignore ]] || fail ".dockerignore"

# The wheel is copied with the files of the dependencies, the only change of
# the generated Dockerfile
WHEEL=${wheel} perl -pi -e 's{^(COPY (?:pyproject\.toml|myapp\.py)\b.*) \./$}{$1 $ENV{WHEEL} ./}' Dockerfile
grep -q "^COPY .*${wheel} \./$" Dockerfile || fail "wheel in Dockerfile"
cat Dockerfile

docker build --quiet --tag "${name}" . >/dev/null
docker run --detach --name "${name}" --publish 127.0.0.1::3000 "${name}" >/dev/null
port=$(docker port "${name}" 3000/tcp | perl -ne 'print $1 and last if /:(\d+)$/')
url=http://127.0.0.1:${port}

# The server listens once its workers are started
for _ in $(seq 120); do
  curl --silent --fail --output /dev/null "${url}/" && break
  sleep 0.5
done

for page in "${pages[@]}"; do
  curl --silent --fail "${url}${page}" | grep -q 'Welcome to the Pyjoyment real-time web framework!' ||
    fail "GET ${page}"
  echo "ok - GET ${page}"
done

if [[ ${#options[@]} -gt 0 ]]; then
  user=$(docker inspect --format '{{.Config.User}}' "${name}")
  [[ ${user} == app ]] || fail "user ${user}"
  echo "ok - user ${user}"
fi

# TERM of docker stop is a graceful shutdown, well before the KILL after 10 seconds
start=${SECONDS}
docker stop --time 10 "${name}" >/dev/null
elapsed=$((SECONDS - start))
[[ ${elapsed} -lt 5 ]] || fail "stopped in ${elapsed}s"
code=$(docker inspect --format '{{.State.ExitCode}}' "${name}")
[[ ${code} -eq 0 ]] || fail "exit code ${code}"
echo "ok - stopped gracefully in ${elapsed}s"
