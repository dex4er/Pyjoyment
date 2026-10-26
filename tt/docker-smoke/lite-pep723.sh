#!/usr/bin/env bash
# A script of generate lite-app, with the inline metadata of PEP 723 and no
# pyproject.toml, on the port of PORT of the container, as Knative sets it,
# with the HEALTHCHECK of --healthcheck.

# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

python -m Pyjoyment generate lite-app >/dev/null
METADATA="# /// script
# requires-python = \">=3.12\"
# dependencies = [\"Pyjoyment\"]
$(echo "${sources}" | perl -pe 's/^/# /')
# ///" perl -0pi -e 's/\A(#!.*\n)/$1$ENV{METADATA}\n/' myapp.py
lock
python myapp.py generate dockerfile --healthcheck / >/dev/null
smoke_dockerfile --port 9090 --health / /
