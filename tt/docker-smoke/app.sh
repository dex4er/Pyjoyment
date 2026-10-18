#!/usr/bin/env bash
# An application of generate app, run as python -m MyApp, with --user app and
# the graceful timeout of the image, which the workers of prefork take.

# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

python -m Pyjoyment generate app >/dev/null
cd my_app
lock
python -m MyApp generate dockerfile --user app --graceful-timeout 8 >/dev/null
smoke_dockerfile --user app / /index.html

# The workers stopped with the graceful timeout of PYJO_GRACEFUL_TIMEOUT of the
# image
docker logs "${name}" 2>&1 | grep -q 'gracefully (8 seconds)' || fail "graceful timeout"
echo "ok - graceful timeout of the image"
