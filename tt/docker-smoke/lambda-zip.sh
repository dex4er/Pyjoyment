#!/usr/bin/env bash
# A script of generate lite-app that ends with handler = app.start(), in the
# ZIP files of "generate lambda-zip" for the architecture of Docker, extracted
# where Lambda extracts them in the image of the custom runtime provided.al2023,
# the layer of Python in /opt and the function in /var/task, whose emulator of
# the Runtime API runs the bootstrap of the function, invoked with the events of
# HTTP requests, buffered and streaming, and whose Python finds the
# certificates of the system.

# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

dir=$(cd "$(dirname "$0")" && pwd)
image=public.ecr.aws/lambda/provided:al2023

# The containers of the two invoke modes
extra_cleanup() {
  docker rm -f "${name}-stream" >/dev/null 2>&1 || true
}

# The script, which is the runtime as the main program
python -m Pyjoyment generate lite-app >/dev/null
perl -pi -e 's/^app\.start\(\)$/handler = app.start()/' myapp.py
grep -q '^handler = app.start()$' myapp.py || fail "handler in myapp.py"
python myapp.py generate pyproject >/dev/null
lock

case $(docker info --format '{{.Architecture}}') in
  aarch64 | arm64) arch=arm64 ;;
  *) arch=x86_64 ;;
esac
python myapp.py generate lambda-zip --arch "${arch}"

mkdir "${work}/opt" "${work}/task"
unzip -q dist/python.zip -d "${work}/opt"
unzip -q dist/function.zip -d "${work}/task"
[[ -x ${work}/task/bootstrap ]] || fail "bootstrap"
cat "${work}/task/bootstrap"
interpreter=$(perl -ne 'print $1 if m{^exec (/opt/python/bin/\S+) myapp\.py$}' "${work}/task/bootstrap")
[[ -n ${interpreter} && -x ${work}${interpreter} ]] || fail "interpreter of the bootstrap"
echo "ok - bootstrap with ${interpreter}"

for mode in BUFFERED RESPONSE_STREAM; do
  container=${name}
  [[ ${mode} == BUFFERED ]] || container=${name}-stream
  docker run --detach --name "${container}" --publish 127.0.0.1::8080 --env "PYJO_LAMBDA_INVOKE_MODE=${mode}" \
    --volume "${work}/opt:/opt:ro" --volume "${work}/task:/var/task:ro" \
    --entrypoint /usr/local/bin/aws-lambda-rie "${image}" /var/task/bootstrap >/dev/null
  port=$(docker port "${container}" 8080/tcp | perl -ne 'print $1 and last if /:(\d+)$/')

  # The events of the payload formats 2.0, of Function URLs, and 1.0, of REST
  # APIs with a stage
  for event in "${dir}"/events/*.json; do
    if [[ ${mode} == BUFFERED ]]; then
      python "${dir}/invoke.py" "http://127.0.0.1:${port}/2015-03-31/functions/function/invocations" "${event}"
    else
      python "${dir}/invoke.py" --stream "http://127.0.0.1:${port}/2015-03-31/functions/function/invocations" "${event}"
    fi
  done
done

# The OpenSSL of python-build-standalone reads the certificates of /etc/ssl,
# which Amazon Linux links to its own
docker exec "${name}" "${interpreter}" -c \
  'import ssl, sys; sys.exit(not ssl.create_default_context().cert_store_stats()["x509_ca"])' ||
  fail "certificates of the system"
echo "ok - certificates of the system"
