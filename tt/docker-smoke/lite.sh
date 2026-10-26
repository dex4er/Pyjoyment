#!/usr/bin/env bash
# A script of generate lite-app, with the pyproject.toml of generate
# pyproject, in an image of another port, with the plugin Health, whose
# liveness the HEALTHCHECK of the image requests.

# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

python -m Pyjoyment generate lite-app >/dev/null
perl -0pi -e "s/^(from Pyjoyment\.Lite import \*\n)/\$1\nplugin('Health')\n/m" myapp.py
grep -q "^plugin('Health')$" myapp.py || fail "plugin Health"
python myapp.py generate pyproject >/dev/null
lock
python myapp.py generate dockerfile --port 8080 >/dev/null
smoke_dockerfile --expose 8080 --health /livez /
