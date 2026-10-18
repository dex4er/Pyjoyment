#!/usr/bin/env bash
# Smoke test of the images of Pyjoyment: runs the script of a variant, which
# generates an application, builds its image with the wheel of the checkout,
# runs it and checks it. The only entry point of the workflow Docker Smoke
# Test.
#
# Usage: tt/docker-smoke/smoke.sh app|lite|lite-pep723|lambda|fastcgi
#
#   app           generate app, run as python -m MyApp, with --user app
#   lite          generate lite-app, with generate pyproject
#   lite-pep723   generate lite-app, with the inline metadata of PEP 723
#   lambda        generate lite-app, with handler = app.start(), on AWS Lambda
#   fastcgi       generate lite-app, listening for FastCGI, behind Caddy
#
# It needs docker, python and uv on PATH, as "mise exec --" gives them.

set -euo pipefail

variant=${1:?Usage: $0 app|lite|lite-pep723|lambda|fastcgi}
dir=$(cd "$(dirname "$0")" && pwd)

[[ ${variant} =~ ^[a-z0-9-]+$ && -x ${dir}/${variant}.sh ]] || {
  echo "not ok - unknown variant ${variant}" >&2
  exit 1
}
exec "${dir}/${variant}.sh"
