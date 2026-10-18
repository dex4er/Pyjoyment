#!/usr/bin/env bash
# An application of generate app, run as python -m MyApp, with --user app.

# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

python -m Pyjoyment generate app >/dev/null
cd my_app
lock
python -m MyApp generate dockerfile --user app >/dev/null
smoke_dockerfile --user app / /index.html
