#!/usr/bin/env bash
# A script of generate lite-app, with the pyproject.toml of generate
# pyproject.

# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

python -m Pyjoyment generate lite-app >/dev/null
python myapp.py generate pyproject >/dev/null
lock
python myapp.py generate dockerfile >/dev/null
smoke_dockerfile /
