#!/usr/bin/env bash
# An application of generate app, run as python -m MyApp, with --user app and
# the graceful timeout of the image, which the workers of prefork take, and
# the plugin Health, whose liveness the HEALTHCHECK of the image requests.

# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

python -m Pyjoyment generate app >/dev/null
cd my_app
perl -0pi -e "s/^(        config = self\.plugin\('YAMLConfig'\)\n)/\$1        self.plugin('Health')\n/m" MyApp/__init__.py
grep -q "self.plugin('Health')" MyApp/__init__.py || fail "plugin Health"
lock
python -m MyApp generate dockerfile --user app --graceful-timeout 8 >/dev/null
smoke_dockerfile --user app --health /livez / /index.html

# The workers stopped with the graceful timeout of PYJO_GRACEFUL_TIMEOUT of the
# image, in the logs that are read whole, as grep -q that stops reading them
# would fail the pipe of docker logs with pipefail
logs=$(docker logs "${name}" 2>&1)
grep -q 'gracefully (8 seconds)' <<<"${logs}" || fail "graceful timeout"
echo "ok - graceful timeout of the image"
