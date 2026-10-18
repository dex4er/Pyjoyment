# shellcheck shell=bash
# The steps that the variants of the smoke test share, which a variant
# sources: a temporary project, the wheel of the checkout, the image of
# "generate dockerfile" and its checks.

set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
work=$(mktemp -d)
name=pyjo-smoke-$(basename "$0" .sh)

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

# The dependencies of the project or of the script with the wheel of the
# checkout, locked
lock() {
  cp "${work}/wheel/${wheel}" .
  if [[ -f pyproject.toml ]]; then
    printf '\n%s\n' "${sources}" >>pyproject.toml
    uv lock --quiet
  else
    uv lock --quiet --script myapp.py
  fi
}

# The image of "generate dockerfile", with the wheel copied with the files of
# the dependencies, the only change of the generated Dockerfile, which serves
# the pages and stops gracefully on the TERM of docker stop
#
#   smoke_dockerfile [--user USER] PAGE...
smoke_dockerfile() {
  local user=
  if [[ ${1:-} == --user ]]; then
    user=$2
    shift 2
  fi

  [[ -f .dockerignore ]] || fail ".dockerignore"
  WHEEL=${wheel} perl -pi -e 's{^(COPY (?:pyproject\.toml|myapp\.py)\b.*) \./$}{$1 $ENV{WHEEL} ./}' Dockerfile
  grep -q "^COPY .*${wheel} \./$" Dockerfile || fail "wheel in Dockerfile"
  cat Dockerfile

  docker build --progress plain --tag "${name}" .
  docker run --detach --name "${name}" --publish 127.0.0.1::3000 "${name}" >/dev/null
  local port url
  port=$(docker port "${name}" 3000/tcp | perl -ne 'print $1 and last if /:(\d+)$/')
  url=http://127.0.0.1:${port}

  # The server listens once its workers are started
  for _ in $(seq 120); do
    curl --silent --fail --output /dev/null "${url}/" && break
    sleep 0.5
  done

  local page
  for page in "$@"; do
    curl --silent --fail "${url}${page}" | grep -q 'Welcome to the Pyjoyment real-time web framework!' ||
      fail "GET ${page}"
    echo "ok - GET ${page}"
  done

  if [[ -n ${user} ]]; then
    local config
    config=$(docker inspect --format '{{.Config.User}}' "${name}")
    [[ ${config} == "${user}" ]] || fail "user ${config}"
    echo "ok - user ${config}"
  fi

  # TERM of docker stop is a graceful shutdown, well before the KILL after 10
  # seconds
  local start elapsed code
  start=${SECONDS}
  docker stop --time 10 "${name}" >/dev/null
  elapsed=$((SECONDS - start))
  [[ ${elapsed} -lt 5 ]] || fail "stopped in ${elapsed}s"
  code=$(docker inspect --format '{{.State.ExitCode}}' "${name}")
  [[ ${code} -eq 0 ]] || fail "exit code ${code}"
  echo "ok - stopped gracefully in ${elapsed}s"
}
