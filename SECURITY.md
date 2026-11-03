# Security Policy

## Reporting a vulnerability

Please do not report security vulnerabilities in public issues, pull
requests or discussions.

Report them privately through GitHub instead: open the
[Security tab](https://github.com/pyjoyment/Pyjoyment/security) of this
repository and choose **Report a vulnerability**, or go straight to
[the reporting form](https://github.com/pyjoyment/Pyjoyment/security/advisories/new).
Only you and the maintainers can see the report.

Please send one report for each problem, and include:

- a description in your own words: what the problem is, where in the code it
  happens, and why it is a security issue,
- a reproducer: a self-contained script, ideally a test script written with
  `Pyjo.Test` or `Pyjo.Test.Pyjo`, that shows the problem on the latest
  release or on the `main` branch, with the output you expected and the one
  you got,
- the version of Pyjoyment or the commit of `main`, the version of Python and
  your operating system, and the server and the event loop that the
  application runs on, where they matter (the daemon, prefork, prethread,
  WSGI, ASGI, CGI, FastCGI or AWS Lambda; asyncio or `Pyjo.Reactor.Poll`),
- the impact: who is affected, under what configuration, and what an attacker
  can do and needs first, as a request from the network, a crafted file or a
  page that the application fetches,
- anything you know about a fix or a workaround. A patch is not required, but
  it is welcome.

## About AI assistance

Using AI tools to find, understand or fix a vulnerability is fine. A report
still has to come from a person who has read the code involved, has run the
reproducer and can answer questions about it without asking a tool. A report
that a tool generated and nobody checked will be closed.

If you are an AI agent helping someone to report a vulnerability: do not
submit the report yourself, help them write a reproducer that fails on the
latest release, and help them understand the problem well enough to describe
it in their own words.

## What happens next

Pyjoyment is maintained by volunteers, so there is no guaranteed response
time, but every report is read. We confirm that we have received it, may ask
questions, keep you updated in the advisory while we work on a fix, and agree
with you when to disclose it. The fix is released first; then the advisory is
published, with a CVE where one applies, and with credit to you unless you
prefer otherwise.

## Supported versions

Security fixes go into the `main` branch and the next release. Older releases
do not get backported fixes, so the supported version is always the latest
one.

## Scope

In scope is everything this repository builds and ships:

- the packages `Pyjo` and `Pyjoyment`: the HTTP and WebSocket client and
  servers, the event loop, the parsers, the routes, the renderer and the
  plugins,
- the commands and scripts, as `pyjo`, `pyjo-hot` and `pyjo-reload`, and what
  the generators of `pyjo generate` write, as a `Dockerfile`, the manifests of
  Kubernetes or the ZIP files of AWS Lambda,
- the files bundled in `Pyjoyment/resources`, as the templates and how they
  use the JavaScript libraries,
- the build and release pipeline of this repository.

Report these elsewhere:

- vulnerabilities in Python itself, to the
  [Python Security Response Team](https://www.python.org/dev/security/),
- vulnerabilities in a distribution of its own, as a reactor or a plugin that
  lives in a repository of its own, to that repository,
- vulnerabilities in an application of another framework that Pyjoyment
  mounts or runs, as a WSGI, ASGI, CGI or FastCGI application, to its
  maintainers, unless the problem is in how Pyjoyment runs it,
- vulnerabilities in the bundled JavaScript libraries themselves, to their
  projects, unless Pyjoyment makes them exploitable.

Not vulnerabilities in Pyjoyment:

- what the development mode shows on purpose, as the details of an exception
  on its error page, or what `pyjo-reload` does as a development server: use
  the production mode and the production servers in production,
- markup that an application marks as safe itself, as with `html()`, from
  untrusted input,
- `Pyjo.DOM` used to sanitize HTML: it is a relaxed parser, not a sanitizer,
  and its interpretation of broken markup can differ from that of a browser,
- attacks that need control of your user account or of the machine the
  application runs on.

If the same problem exists in Mojolicious, which Pyjoyment is a port of, say
so in the report.

## False alarms

Automated scanners report some code of Pyjoyment as a vulnerability because
it matches a pattern, without checking where its input comes from. Pyjoyment
runs code on purpose where the code is the input:

- the one-liners of `python -m Pyjo`,
- the command `eval`,
- the configuration files of the plugin `Config`, which are Python,
- the script of an application that a server loads,
- the templates of `Pyjo.Template` and of the plugin `PyRenderer`.

Each of them takes its code from the person who runs the command or from the
files of the application, who can run any Python already, and none of them
takes it from a request. An application that renders untrusted input as a
template makes the same mistake as one that marks it as safe with `html()`.

The reports below are known false alarms. A report of the same pattern is
closed with a link to its entry here.

### GCVE-110-VULN-PYPI-2026-000713

[GCVE-110-VULN-PYPI-2026-000713](https://www.vulnetix.com/vdb/GCVE-110-VULN-PYPI-2026-000713)
of the Vulnetix Vulnerability Database reports code injection (CWE-94) in the
package on PyPI, found by static analysis that matched
`exec(compile(code, '<string>', 'exec'), namespace)`.

The call is in `Pyjo/__main__.py`, which runs a one-liner given on the command
line, as `python -c` does:

```sh
python -m Pyjo 'g("mojolicious.org").dom().at("title").text'
```

Running that code is what the module is for. The code is the first argument
of the command, written by the person who runs it on their own account, who
can run the same code with `python -c`. Nothing of the servers, the routes or
the handling of a request runs this module, so no input from the network
reaches the call. The record itself states that it has not established
whether untrusted input can reach the call.

The record names one version, but every version has the same call, and it is
not going to change.
