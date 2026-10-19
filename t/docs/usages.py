import Pyjo.File
import Pyjo.GetOpt
import Pyjo.Server.Hot
import Pyjo.Server.Reload
import Pyjo.Util
import Pyjoyment
import Pyjoyment.Command
import Pyjoyment.Commands

from Pyjo.Test import *
from Pyjo.Util import extract_usage

import contextlib
import importlib
import io
import os
import pkgutil
import re
import sys


# The usages of the commands and of the scripts of the servers, which their documentation has, against the options
# that they parse: the options of a usage are the ones of getopt, and its blocks of options are laid out as
# format_usage lays them out. A failure shows the usage laid out, which goes into the docstring.

# The options shared by all commands, which Pyjoyment.Commands parses
SHARED = {'help', 'home', 'log-format', 'mode'}

_RE_LABEL = re.compile(r'^  (?:-(\w)(?:, --([\w-]+))?|    --([\w-]+))(?: (\[)?(<)[^>]+>\]?)?(?:\s|$)')


def documented(usage):
    # The options of the blocks of a usage, as the names and whether a value is none, required or optional
    options = {}
    in_block = False
    for line in usage.split('\n'):
        if re.match(r'^Options\b[^:]*:$', line):
            in_block = True
        elif not line.strip():
            in_block = False
        elif in_block and (m := _RE_LABEL.match(line)):
            names = frozenset(name for name in (m[1], m[2], m[3]) if name)
            value = 'optional' if m[4] else 'required' if m[5] else None
            options[max(names, key=len)] = (names, value)
    return options


def specified(specs):
    # The options of the specifications of getopt, in the same form
    options = {}
    for spec in specs:
        m = re.fullmatch(r'([\w|?-]+)([=:][sif][@%]?|!|\+)?', spec)
        names = frozenset(m[1].split('|'))
        value = 'required' if (m[2] or '').startswith('=') else 'optional' if (m[2] or '').startswith(':') else None
        options[max(names, key=len)] = (names, value)
    return options


@contextlib.contextmanager
def captured(*modules):
    # The specifications that modules pass to getopt, which still parses the arguments
    specs = []
    getopt = Pyjo.Util.getopt

    def capture(*args, **kwargs):
        specs.extend(args[1] if len(args) > 1 and isinstance(args[1], dict) else args[0])
        return getopt(*args, **kwargs)

    for module in modules:
        module.getopt = capture
    try:
        yield specs
    finally:
        for module in modules:
            module.getopt = getopt


def check(name, usage, specs, shared=frozenset()):
    with subtest(name):
        is_ok(Pyjo.GetOpt.format_usage(usage), usage, 'laid out') or diag(Pyjo.GetOpt.format_usage(usage))
        options = documented(usage)
        expected = specified(specs)
        for option in sorted(set(options) & shared):
            expected[option] = options[option]
        is_deeply_ok(
            {name: (sorted(names), value) for name, (names, value) in options.items()},
            {name: (sorted(names), value) for name, (names, value) in expected.items()},
            'options of getopt',
        )


app = Pyjoyment.new()
app.log.level = 'fatal'
cwd = os.getcwd()
dir = Pyjo.File.tempdir()

# The commands, run with an unknown option in a temporary directory, as getopt rejects it before they do anything; a
# command without getopt has no options of its own
for package in ('Pyjoyment.Command', 'Pyjoyment.Command.Author', 'Pyjoyment.Command.Author.generate'):
    for info in pkgutil.iter_modules(importlib.import_module(package).__path__):
        module = importlib.import_module(f'{package}.{info.name}')
        cls = getattr(module, 'object', None)
        if not isinstance(cls, type) or not issubclass(cls, Pyjoyment.Command.object):
            continue
        specs = []
        # The modules of the command and of the classes it inherits from, as one that calls getopt in a method of its own
        modules = [m for m in dict.fromkeys(sys.modules[c.__module__] for c in cls.__mro__) if hasattr(m, 'getopt')]
        if modules:
            os.chdir(dir.to_str())
            try:
                with (
                    captured(*modules) as specs,
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(io.StringIO()),
                    contextlib.suppress(BaseException),
                ):
                    cls.new(app=app).run('--pyjo-usage-check')
            finally:
                os.chdir(cwd)
        shared = SHARED if set(documented(cls.usage)) & (SHARED - {'help'}) else frozenset({'help'})
        check(module.__name__, cls.usage, specs, shared)

# The options shared by all commands
with captured(Pyjoyment.Commands) as specs:
    Pyjoyment.Commands._args([])
check('Pyjoyment.Commands', extract_usage(Pyjoyment.Commands.__file__), specs)

# The scripts of the servers, whose usage is a section of the docstring of the module
for module, section in ((Pyjo.Server.Reload, 'pyjo-reload'), (Pyjo.Server.Hot, 'pyjo-hot')):
    with (
        captured(module) as specs,
        contextlib.redirect_stderr(io.StringIO()),
        contextlib.suppress(SystemExit),
    ):
        module.main(['--pyjo-usage-check'])
    check(section, extract_usage(module.__file__, section=section), specs)

ok(not os.listdir(dir.to_str()), 'nothing written')

done_testing()
