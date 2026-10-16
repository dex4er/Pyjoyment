r"""
Pyjo.Prove - Run test scripts
=============================
::

    $ python -m Pyjo.Prove t/Pyjo t/docs
    $ python -m Pyjo.Prove -r -j 4 t
    $ pyjo-prove -v t/Pyjo/URL.py

:mod:`Pyjo.Prove` runs test scripts which print the
`Test Anything Protocol <https://testanything.org/>`_ (TAP), such as the ones
written with :mod:`Pyjo.Test`, and reports their results. It is inspired by
Perl's ``prove`` and accepts the options of it that make sense for Python.

A directory runs every script with the extension ``.py`` in it, and with
``-r`` in its subdirectories too. Without arguments it runs ``t``.

A test script passes when it exits with status ``0``, declares a plan, runs as
many tests as planned and none of them fails, except the ``TODO`` tests. A
plan of ``1..0 # SKIP reason`` skips the whole script. ``Bail out!`` stops the
whole run. Indented lines belong to subtests and are not parsed: the parent
test point stands for the whole subtest.

A script with the inline metadata of
`PEP 723 <https://peps.python.org/pep-0723/>`_ is skipped without running when
the Python that runs it does not satisfy its ``requires-python``, as a script
with the syntax of a newer Python, which an older one cannot compile, so that
the script cannot skip itself. ::

    # /// script
    # requires-python = ">=3.14"
    # ///

The summary ends with ``Result: PASS`` when every test script passed,
``Result: FAIL`` when one did not, and ``Result: NOTESTS`` when they passed
without running a test, as when every one of them was skipped. The exit status is ``0`` when every test script passed and ``1`` otherwise.
Ctrl-C (``SIGINT``) stops the run: the test scripts that are running are
killed, with the processes they started, and the harness dies of the signal,
or with ``--trap`` prints the summary of the test scripts that have finished.

Options
-------

``-r``, ``--recurse``
    Run the test scripts in subdirectories too.

``-j N``, ``--jobs N``
    Run up to N test scripts at the same time.

``-v``, ``--verbose``
    Print the TAP output of each test script.

``-I DIR``, ``--include DIR``
    Add the directory to ``PYTHONPATH`` of the test scripts. Can be repeated.

``-l``, ``--lib``
    Add the current directory to ``PYTHONPATH`` of the test scripts, as
    ``-I .`` does, where ``prove`` adds ``lib``.

``--ext EXT``
    Extension of the test scripts in a directory, ``.py`` by default.

``--exec CMD``
    Command that runs a test script, the current Python interpreter by default.

``--timeout SECONDS``
    The most time a test script may run, no limit by default. A test script
    that runs longer is killed, with the processes it started, and fails.

``--trap``
    Print the summary of the test scripts that have finished when Ctrl-C
    interrupts the run.

``--capture-stderr``
    Keep the standard error of each test script and print it after the line of
    its result, each line after the name of the script, instead of letting it
    through as the script writes it, where the scripts that run at the same
    time with ``-j`` mix it. ::

        t/Pyjo/URL.py ........ ok
        t/Pyjo/URL.py: ResourceWarning: unclosed <socket.socket ...>

    ``prove`` has no such option: its ``--merge`` puts the standard error into
    the TAP output, which shows it with ``-v`` only.

``--stderr-lines N``
    With ``--capture-stderr``, print at most N lines of the standard error of
    a test script, no limit by default: the first half of them and the last
    half, which ends with what the script said last, and between them a line
    that tells how many were left out. ::

        t/Pyjo/URL.py: [922554 lines left out]

``--count``, ``--no-count``, ``--nocount``
    Show the X/Y count of the tests of a test script while it runs or not,
    renewed once a second. By default it is shown when the output goes to a
    terminal, and never with ``-v``. With ``-j``, a line shows the number of
    the tests of all the test scripts, the seconds of the run and the count of
    each test script that runs. ::

        t/Pyjo/URL.py ........ 12/?
        ===(     158;3  12/?  40/40  3/? )======================================

    ``prove`` shows it on a terminal only, even with ``--count``.

``-c``, ``--color``, ``--no-color``, ``--nocolor``
    Color the output or not. By default it is colored when it goes to a
    terminal, unless ``NO_COLOR`` is set or ``TERM`` is ``dumb``: the result of
    a test script that passed and the summary of a run that passed are green,
    what failed is red, what was skipped and the ``TODO`` tests are yellow, and
    so is ``NOTESTS``. With ``--capture-stderr``, the standard error of a
    test script is red.

Environment
-----------

``PYJO_PROVE_OPTS``
    Options that go before the ones of the command line, which override them,
    split as a shell splits words. The test scripts do not get it, so that a
    test script that runs :mod:`Pyjo.Prove` itself runs it without them. ::

        $ PYJO_PROVE_OPTS='-l -j 4' python -m Pyjo.Prove -r t

    ``prove`` reads its options from ``.proverc`` instead.

Functions
---------
"""

import argparse
import asyncio
import collections
import operator
import os
import re
import shlex
import signal
import sys
import time
import tomllib

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TextIO


__all__ = ['Result', 'find_scripts', 'finish', 'main', 'parse', 'run', 'run_script']


RE_VERSION = re.compile(r'TAP version (\d+)\s*$')
RE_PLAN = re.compile(r'1\.\.(\d+)\s*(?:#\s*(.*?))?\s*$')
RE_TEST = re.compile(
    r'(not )?ok\b\s*(\d+)?\s*(?:-\s*)?((?:\\.|[^#\\])*?)\s*(?:#\s*(skip|todo)\b\s*(.*?))?\s*$',
    re.IGNORECASE,
)
RE_BAIL_OUT = re.compile(r'Bail out!\s*(.*?)\s*$')
RE_SKIP = re.compile(r'skip\b\s*(.*)', re.IGNORECASE)
RE_METADATA = re.compile(r'(?m)^# /// (?P<type>[a-zA-Z0-9-]+)$\s(?P<content>(^#(| .*)$\s)+)^# ///$')
RE_SPECIFIER = re.compile(r'\s*(~=|===|==|!=|<=|>=|<|>)\s*v?(\d+(?:\.\d+)*)(\.\*)?\s*')


@dataclass
class Result:
    """
    Result of a test script: what its TAP output says and how it exited.
    """

    path: str
    planned: int | None = None
    skip_all: str | None = None
    tests: int = 0
    failed: list[int] = field(default_factory=lambda: [])
    todo_passed: list[int] = field(default_factory=lambda: [])
    skipped: int = 0
    bail_out: str | None = None
    exit_status: int = 0
    timed_out: float | None = None
    errors: list[str] = field(default_factory=lambda: [])
    output: list[str] = field(default_factory=lambda: [])
    stderr: list[str] = field(default_factory=lambda: [])
    stderr_left_out: int = 0

    @property
    def passed(self) -> bool:
        """::

            ok = result.passed

        True if the test script passed.
        """
        return not self.failed and not self.errors and self.bail_out is None


def parse(result: Result, line: str) -> None:
    """::

        result = Result('t/test.py')
        for line in output.splitlines():
            parse(result, line)

    Parse a line of TAP output into the result.
    """
    result.output.append(line)

    if not line or line[0].isspace():
        return

    if m := RE_TEST.match(line):
        not_ok, number, _, directive, _ = m.groups()
        result.tests += 1
        if number is not None and int(number) != result.tests:
            result.errors.append(f'Tests out of sequence.  Found ({number}) but expected ({result.tests})')
        directive = (directive or '').lower()
        if directive == 'skip':
            result.skipped += 1
        if not_ok and directive != 'todo':
            result.failed.append(result.tests)
        if not not_ok and directive == 'todo':
            result.todo_passed.append(result.tests)
        return

    if m := RE_PLAN.match(line):
        if result.planned is not None:
            result.errors.append('More than one plan found in TAP output')
            return
        result.planned = int(m.group(1))
        if result.planned == 0 and (skip := RE_SKIP.match(m.group(2) or '')):
            result.skip_all = skip.group(1)
        return

    if m := RE_BAIL_OUT.match(line):
        result.bail_out = m.group(1)
        return

    if RE_VERSION.match(line) and len(result.output) > 1:
        result.errors.append('TAP version must be the first line of the output')


def finish(result: Result) -> None:
    """::

        finish(result)

    Check the result once the test script has exited: the plan, the number of
    tests and the exit status.
    """
    if result.bail_out is not None:
        return
    if result.timed_out is not None:
        result.errors.append(f'Timed out after {result.timed_out:g} seconds')
        return
    if result.planned is None:
        result.errors.append('No plan found in TAP output')
    elif result.planned != result.tests:
        result.errors.append(f'Bad plan.  You planned {result.planned} tests but ran {result.tests}.')
    if result.exit_status:
        result.errors.append(f'Non-zero exit status: {result.exit_status}')


async def run_script(
    path: str,
    command: Sequence[str],
    env: dict[str, str],
    *,
    verbose: bool = False,
    stream: bool = False,
    timeout: float | None = None,
    capture_stderr: bool = False,
    stderr_lines: int | None = None,
    color: bool = False,
    progress: Callable[[Result], object] | None = None,
) -> Result:
    """::

        result = await run_script('t/test.py', [sys.executable], dict(os.environ))
        result = await run_script('t/test.py', [sys.executable], dict(os.environ), timeout=60)
        result = await run_script('t/test.py', [sys.executable], dict(os.environ), capture_stderr=True)
        result = await run_script('t/test.py', [sys.executable], dict(os.environ), capture_stderr=True, stderr_lines=100)
        result = await run_script('t/test.py', [sys.executable], dict(os.environ), progress=print)

    Run a test script and parse its TAP output. The standard error of the
    script goes to the standard error of this process, or with
    ``capture_stderr`` to the lines of :attr:`Result.stderr`, at most
    ``stderr_lines`` of them, the first half and the last half, with the number
    of the lines between them in :attr:`Result.stderr_left_out`. With ``verbose``
    and ``stream``, the TAP output is printed as it comes, colored with
    ``color``. ``progress`` is called with the result when the script starts
    and after each of its tests. A script that runs
    longer than ``timeout`` seconds is killed, with the processes it started.
    A script whose ``requires-python`` the Python of the command does not
    satisfy is skipped without running.
    """
    result = Result(path)
    try:
        requires = _requires_python(path)
        if requires is not None and (version := await _python(command)) is not None:
            if not _satisfies(version, requires):
                result.planned = 0
                result.skip_all = f'requires Python {requires}'
                return result
    except ValueError as e:
        result.errors.append(f'Invalid script metadata: {e}')
        return result

    # The script leads a process group of its own, so that the processes it starts are killed with it
    process = await asyncio.create_subprocess_exec(
        *command,
        path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE if capture_stderr else None,
        env=env,
        process_group=0 if hasattr(os, 'killpg') else None,
    )
    assert process.stdout is not None
    if progress is not None:
        progress(result)
    stderr = (
        asyncio.create_task(_read_lines(process.stderr, result, stderr_lines)) if process.stderr is not None else None
    )
    try:
        async with asyncio.timeout(timeout):
            while raw := await process.stdout.readline():
                line = raw.decode('utf-8', 'replace').rstrip('\r\n')
                tests = result.tests
                parse(result, line)
                if progress is not None and result.tests != tests:
                    progress(result)
                if verbose and stream:
                    print(_tap_line(line, color), flush=True)
            result.exit_status = await process.wait()
    except TimeoutError:
        result.timed_out = timeout
        _kill(process)
        result.exit_status = await process.wait()
    finally:
        # Ctrl-C reaches the foreground process group only, not the one of the script, which the harness waits for,
        # so that it does not outlive the harness
        if process.returncode is None:
            _kill(process)
            await process.wait()
        # A process that the script started may keep the standard error open after the script exits
        if stderr is not None:
            try:
                await asyncio.wait_for(stderr, 5)
            except TimeoutError:
                pass
    finish(result)
    return result


def find_scripts(paths: Sequence[str], ext: str, recurse: bool) -> list[str]:
    """::

        scripts = find_scripts(['t'], '.py', recurse=True)

    Expand directories into the test scripts in them, sorted by name.
    """
    scripts: list[str] = []
    for path in paths:
        if not os.path.isdir(path):
            scripts.append(path)
            continue
        found: list[str] = []
        for root, dirs, files in os.walk(path):
            dirs.sort()
            found.extend(os.path.join(root, f) for f in files if f.endswith(ext))
            if not recurse:
                break
        scripts.extend(sorted(found))
    return scripts


async def run(
    scripts: Sequence[str],
    command: Sequence[str] | None = None,
    env: dict[str, str] | None = None,
    *,
    jobs: int = 1,
    verbose: bool = False,
    timeout: float | None = None,
    trap: bool = False,
    capture_stderr: bool = False,
    stderr_lines: int | None = None,
    color: bool | None = None,
    count: bool | None = None,
) -> list[Result]:
    """::

        results = asyncio.run(run(['t/a.py', 't/b.py'], jobs=2))
        results = asyncio.run(run(['t/a.py', 't/b.py'], timeout=60, trap=True))
        results = asyncio.run(run(['t/a.py', 't/b.py'], jobs=2, capture_stderr=True))
        results = asyncio.run(run(['t/a.py', 't/b.py'], jobs=2, capture_stderr=True, stderr_lines=1000))
        results = asyncio.run(run(['t/a.py', 't/b.py'], color=False))
        results = asyncio.run(run(['t/a.py', 't/b.py'], count=False))

    Run the test scripts, print a line for each of them and a summary, and
    return the results in the order of the scripts. With ``trap``, a run that
    Ctrl-C interrupts prints the summary and returns the results of the test
    scripts that have finished. The output is colored with ``color``, and the
    tests of the test scripts are counted while they run with ``count``, both
    by default when the output goes to a terminal, the count without
    ``verbose`` only.
    """
    command = list(command or [sys.executable])
    env = dict(os.environ if env is None else env)
    width = max((len(s) for s in scripts), default=0) + 3
    semaphore = asyncio.Semaphore(max(jobs, 1))
    bailed_out = asyncio.Event()
    started = time.monotonic()
    out_color = _color_default(sys.stdout) if color is None else color
    err_color = _color_default(sys.stderr) if color is None else color
    counter = (
        _Count(width, jobs > 1, out_color) if not verbose and (_tty(sys.stdout) if count is None else count) else None
    )

    finished: dict[int, Result] = {}
    interrupted = False

    async def one(i: int, path: str) -> None:
        async with semaphore:
            if bailed_out.is_set():
                return
            stream = jobs <= 1
            if stream and verbose:
                print(f'{path} ..', flush=True)
            result = await run_script(
                path,
                command,
                env,
                verbose=verbose,
                stream=stream,
                timeout=timeout,
                capture_stderr=capture_stderr,
                stderr_lines=stderr_lines,
                color=out_color,
                progress=counter.update if counter is not None else None,
            )
            if counter is not None:
                counter.finish(result)
            if verbose and not stream:
                print(f'{path} ..', *(_tap_line(line, out_color) for line in result.output), sep='\n', flush=True)
            print(_status_line(result, width, out_color), flush=True)
            lines = [f'{path}: {line}' for line in result.stderr]
            if result.stderr_left_out:
                lines.insert(_head(stderr_lines or 0), f'{path}: [{result.stderr_left_out} lines left out]')
            for line in lines:
                print(_paint(line, 'red', err_color), file=sys.stderr, flush=True)
            if counter is not None:
                counter.show(refresh=True)
            if result.bail_out is not None:
                bailed_out.set()
            finished[i] = result

    try:
        if jobs <= 1:
            for i, path in enumerate(scripts):
                await one(i, path)
        else:
            await asyncio.gather(*(one(i, path) for i, path in enumerate(scripts)))
    except asyncio.CancelledError:
        # Ctrl-C, which asyncio.run() turns into the cancellation of the run
        if not trap:
            raise
        interrupted = True
        if counter is not None:
            counter.clear()
        print(flush=True)

    done = [finished[i] for i in sorted(finished)]
    _summary(done, time.monotonic() - started, interrupted, color=out_color, err_color=err_color)
    return done


def main(argv: Sequence[str] | None = None) -> int:
    """::

        sys.exit(main(['-r', 't']))

    Command line interface: parse the options, after the ones of
    ``PYJO_PROVE_OPTS``, run the test scripts and return the exit status.
    """
    parser = argparse.ArgumentParser(prog='pyjo-prove', description='Run test scripts which print TAP.')
    parser.add_argument('-r', '--recurse', action='store_true', help='run the test scripts in subdirectories too')
    parser.add_argument('-j', '--jobs', type=int, default=1, metavar='N', help='run up to N test scripts at once')
    parser.add_argument('-v', '--verbose', action='store_true', help='print the TAP output of each test script')
    parser.add_argument(
        '-I', '--include', action='append', default=[], metavar='DIR', help='add the directory to PYTHONPATH'
    )
    # Unlike prove: the current directory, where the modules of a project of Python are, as prove adds lib
    parser.add_argument(
        '-l', '--lib', dest='include', action='append_const', const='.', help='add the current directory to PYTHONPATH'
    )
    parser.add_argument('--ext', default='.py', help='extension of the test scripts, .py by default')
    parser.add_argument('--exec', dest='command', metavar='CMD', help='command that runs a test script')
    parser.add_argument(
        '--timeout', type=float, metavar='SECONDS', help='the most time a test script may run, no limit by default'
    )
    parser.add_argument('--trap', action='store_true', help='print the summary when Ctrl-C interrupts the run')
    # Not in prove: --capture-stderr, as --merge of prove shows the standard error with -v only, among the TAP output
    parser.add_argument(
        '--capture-stderr', action='store_true', help='print the standard error of a test script after its result'
    )
    # Not in prove: --stderr-lines, for --capture-stderr
    parser.add_argument(
        '--stderr-lines',
        type=_lines,
        metavar='N',
        help='print at most N lines of the standard error of a test script with --capture-stderr',
    )
    parser.add_argument(
        '--count', action='store_const', const=True, help='show the X/Y count of the tests, by default on a terminal'
    )
    parser.add_argument(
        '--no-count', '--nocount', dest='count', action='store_const', const=False, help='do not show the count'
    )
    parser.add_argument(
        '-c', '--color', action='store_const', const=True, help='color the output, by default on a terminal'
    )
    # Both forms, which Getopt::Long of prove accepts for its --nocolor
    parser.add_argument('--no-color', '--nocolor', dest='color', action='store_const', const=False, help='do not color')
    parser.add_argument('paths', nargs='*', default=['t'], help='test scripts and directories, t by default')
    # Not in prove: PYJO_PROVE_OPTS, where prove reads .proverc
    try:
        opts = shlex.split(os.environ.get('PYJO_PROVE_OPTS', ''))
    except ValueError as e:
        parser.error(f'PYJO_PROVE_OPTS: {e}')
    args = parser.parse_args([*opts, *(sys.argv[1:] if argv is None else argv)])

    ext = args.ext if args.ext.startswith('.') else f'.{args.ext}'
    scripts = find_scripts(args.paths, ext, args.recurse)
    if not scripts:
        print('No tests found.', file=sys.stderr)
        return 1

    # A test script that runs the harness does not get the options of this one, as prove leaves out HARNESS_OPTIONS
    env = {name: value for name, value in os.environ.items() if name != 'PYJO_PROVE_OPTS'}
    if args.include:
        env['PYTHONPATH'] = os.pathsep.join([*args.include, *filter(None, [env.get('PYTHONPATH')])])

    command = shlex.split(args.command) if args.command else [sys.executable]
    try:
        results = asyncio.run(
            run(
                scripts,
                command,
                env,
                jobs=args.jobs,
                verbose=args.verbose,
                timeout=args.timeout,
                trap=args.trap,
                capture_stderr=args.capture_stderr,
                stderr_lines=args.stderr_lines,
                color=args.color,
                count=args.count,
            )
        )
    except KeyboardInterrupt:
        # Die of the signal, as a process that does not handle it does, without a traceback
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGINT)
        raise
    return 0 if len(results) == len(scripts) and all(r.passed for r in results) else 1


# The version of the Python that a command runs, asked once for a command other than this Python
_PYTHONS: dict[tuple[str, ...], tuple[int, ...] | None] = {}

_OPERATORS: dict[str, Callable[[tuple[int, ...], tuple[int, ...]], bool]] = {
    '===': operator.eq,
    '==': operator.eq,
    '!=': operator.ne,
    '<=': operator.le,
    '>=': operator.ge,
    '<': operator.lt,
    '>': operator.gt,
}


async def _python(command: Sequence[str]) -> tuple[int, ...] | None:
    key = tuple(command)
    if key not in _PYTHONS:
        if list(command) == [sys.executable]:
            _PYTHONS[key] = tuple(sys.version_info[:3])
        else:
            _PYTHONS[key] = None
            try:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    '-c',
                    'import sys; print(*sys.version_info[:3])',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                out, _ = await process.communicate()
                if process.returncode == 0 and len(version := tuple(int(n) for n in out.split())) == 3:
                    _PYTHONS[key] = version
            except (OSError, ValueError):
                pass
    return _PYTHONS[key]


# The requires-python of the inline metadata of PEP 723, as its reference implementation reads it
def _requires_python(path: str) -> str | None:
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            source = f.read()
    except OSError:
        return None
    blocks = [m for m in RE_METADATA.finditer(source) if m.group('type') == 'script']
    if not blocks:
        return None
    if len(blocks) > 1:
        raise ValueError('Multiple script blocks found')
    content = ''.join(
        line[2:] if line.startswith('# ') else line[1:] for line in blocks[0].group('content').splitlines(keepends=True)
    )
    requires = tomllib.loads(content).get('requires-python')
    if requires is not None and not isinstance(requires, str):
        raise ValueError('requires-python is not a string')
    return requires


# The version specifiers of PEP 440 for a release, without pre-, post- and development releases
def _satisfies(version: tuple[int, ...], specifier: str) -> bool:
    satisfied = True
    for clause in specifier.split(','):
        if (m := RE_SPECIFIER.fullmatch(clause)) is None or (m.group(3) and m.group(1) not in ('==', '!=')):
            raise ValueError(f'Invalid requires-python: {specifier}')
        op, release, wildcard = m.groups()
        want = tuple(int(n) for n in release.split('.'))
        if wildcard:
            satisfied = satisfied and (version[: len(want)] == want) == (op == '==')
        elif op == '~=':
            if len(want) < 2:
                raise ValueError(f'Invalid requires-python: {specifier}')
            satisfied = (
                satisfied and _pad(version, want) >= _pad(want, version) and version[: len(want) - 1] == want[:-1]
            )
        else:
            satisfied = satisfied and _OPERATORS[op](_pad(version, want), _pad(want, version))
    return satisfied


def _pad(version: tuple[int, ...], other: tuple[int, ...]) -> tuple[int, ...]:
    return version + (0,) * (len(other) - len(version))


def _name(path: str, width: int) -> str:
    return f'{path} {"." * (width - len(path))}'


def _status_line(result: Result, width: int, color: bool = False) -> str:
    name = _name(result.path, width)
    if result.bail_out is not None:
        return f'{name} {_paint(f"Bailout called.  Further testing stopped:  {result.bail_out}", "red", color)}'
    if result.timed_out is not None:
        return f'{name} {_paint("Timed out", "red", color)}'
    if result.passed and result.skip_all is not None:
        return f'{name} {_paint(f"skipped: {result.skip_all}", "yellow", color)}'
    if result.passed:
        return f'{name} {_paint("ok", "green", color)}'
    if result.failed:
        return f'{name} {_paint(f"Failed {len(result.failed)}/{result.tests} subtests", "red", color)}'
    return f'{name} {_paint("Dubious", "red", color)}'


# A test point of the TAP output, at any level of subtests: one that failed is red, one with a directive yellow
def _tap_line(line: str, color: bool) -> str:
    if color and (m := RE_TEST.match(line.lstrip())):
        if m.group(4):
            return _paint(line, 'yellow', color)
        if m.group(1):
            return _paint(line, 'red', color)
    return line


_COLORS = {'green': '32', 'red': '31', 'yellow': '33'}


def _paint(text: str, name: str, color: bool) -> str:
    return f'\033[{_COLORS[name]}m{text}\033[0m' if color else text


# Not in prove: NO_COLOR (https://no-color.org) and TERM=dumb, which turn off the colors of Python itself too
def _color_default(stream: TextIO | None) -> bool:
    return _tty(stream) and not os.environ.get('NO_COLOR') and os.environ.get('TERM') != 'dumb'


def _tty(stream: TextIO | None) -> bool:
    try:
        return stream is not None and stream.isatty()
    except (OSError, ValueError):
        return False


# The width of the line of prove for the count of the test scripts that run at the same time
_RULER_WIDTH = 72
_RULER_TRAILER = '... )==='


class _Count:
    # The X/Y count of the tests of the test scripts that run, on a line that a carriage return renews, at most once a
    # second, as prove does: the count of the one test script that runs, or with jobs, a line of all of them
    def __init__(self, width: int, parallel: bool, color: bool) -> None:
        self.width = width
        self.parallel = parallel
        self.color = color
        self.active: dict[int, Result] = {}
        self.counted: dict[int, int] = {}
        self.tests = 0
        self.started = time.monotonic()
        self.second: int | None = None
        self.length = 0

    def update(self, result: Result) -> None:
        key = id(result)
        if key not in self.active:
            self.active[key] = result
            self.counted[key] = 0
            if not self.parallel:
                self.second = None
                self._write(f'{_name(result.path, self.width)} ')
            else:
                self.show(refresh=True)
            return
        self.tests += result.tests - self.counted[key]
        self.counted[key] = result.tests
        self.show()

    def finish(self, result: Result) -> None:
        self.active.pop(id(result), None)
        self.counted.pop(id(result), None)
        self.clear()

    def show(self, refresh: bool = False) -> None:
        second = int(time.monotonic())
        if not self.active or (second == self.second and not refresh):
            return
        self.second = second
        if not self.parallel:
            result = next(iter(self.active.values()))
            name = f'{_name(result.path, self.width)} '
            count = f'{result.tests}/{result.planned or "?"} '
            self._write(f'{name}{_paint(count, "red", self.color and bool(result.failed))}', len(name) + len(count))
            return
        ruler = f'===( {self.tests:7d};{int(time.monotonic() - self.started)}  '
        for r in self.active.values():
            planned = str(r.planned or '?')
            ruler += f'{r.tests:{len(planned)}d}/{planned}  '
        ruler = f'{ruler[:-1]})==='
        if len(ruler) > _RULER_WIDTH:
            ruler = ruler[: _RULER_WIDTH - len(_RULER_TRAILER)] + _RULER_TRAILER
        self._write(ruler.ljust(_RULER_WIDTH, '='))

    def clear(self) -> None:
        if self.length:
            sys.stdout.write(f'\r{" " * self.length}\r')
            sys.stdout.flush()
            self.length = 0

    # The length is the one on the screen, without the escape sequences of the colors
    def _write(self, line: str, length: int | None = None) -> None:
        sys.stdout.write(f'\r{line}')
        sys.stdout.flush()
        self.length = len(line) if length is None else length


# The first half of the lines, and the last half in a queue that leaves out the lines before them
async def _read_lines(stream: asyncio.StreamReader, result: Result, limit: int | None) -> None:
    head = None if limit is None else _head(limit)
    tail = collections.deque[str](maxlen=None if limit is None else limit // 2)
    try:
        while raw := await stream.readline():
            line = raw.decode('utf-8', 'replace').rstrip('\r\n')
            if head is None or len(result.stderr) < head:
                result.stderr.append(line)
                continue
            if len(tail) == tail.maxlen:
                result.stderr_left_out += 1
            tail.append(line)
    finally:
        result.stderr.extend(tail)


def _head(limit: int) -> int:
    return (limit + 1) // 2


def _lines(value: str) -> int:
    if (lines := int(value)) < 0:
        raise argparse.ArgumentTypeError(f'invalid number of lines: {value}')
    return lines


def _kill(process: asyncio.subprocess.Process) -> None:
    try:
        if hasattr(os, 'killpg'):
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        pass


def _summary(
    results: list[Result], elapsed: float, interrupted: bool = False, *, color: bool = False, err_color: bool = False
) -> None:
    failed = [r for r in results if not r.passed]
    tests = sum(r.tests for r in results)

    if interrupted:
        print(_paint('Test run interrupted!', 'red', err_color), file=sys.stderr, flush=True)

    if failed:
        print('\nTest Summary Report\n-------------------')
        for r in failed:
            print(f'{r.path} (Tests: {r.tests} Failed: {len(r.failed)})')
            if r.failed:
                failures = f'Failed {"tests" if len(r.failed) > 1 else "test"}:  {", ".join(map(str, r.failed))}'
                print(f'  {_paint(failures, "red", color)}')
            if r.bail_out is not None:
                print(f'  {_paint(f"Bail out:  {r.bail_out}", "red", color)}')
            for error in r.errors:
                print(f'  {_paint(error, "red", color)}')
    elif not interrupted:
        print(_paint('All tests successful.', 'green', color))

    todo_passed = [r for r in results if r.todo_passed]
    for r in todo_passed:
        print(_paint(f'{r.path}: TODO passed:  {", ".join(map(str, r.todo_passed))}', 'yellow', color))

    print(f'Files={len(results)}, Tests={tests}, {elapsed:.0f} wallclock secs')
    status, name = ('FAIL', 'red') if failed or interrupted else ('PASS', 'green') if tests else ('NOTESTS', 'yellow')
    print(f'Result: {_paint(status, name, color)}', flush=True)


if __name__ == '__main__':
    sys.exit(main())
