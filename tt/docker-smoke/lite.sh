#!/usr/bin/env bash
# A script of generate lite-app, with the pyproject.toml of generate
# pyproject, in an image of another port.

# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

python -m Pyjoyment generate lite-app >/dev/null
python myapp.py generate pyproject >/dev/null
lock
python myapp.py generate dockerfile --port 8080 >/dev/null
smoke_dockerfile --expose 8080 /
