import Pyjo.File
import Pyjoyment
import Pyjoyment.Command.Author.generate.plugin

from Pyjo.Test import *

import contextlib
import io
import os
import subprocess
import sys
import tomllib


# The modules of the checkout for the tests of the generated plugin, which run in a process of their own
root = Pyjo.File.path(__file__).to_abs().dirname().dirname().dirname().to_str()
env = {**os.environ, 'PYTHONPATH': os.pathsep.join([root, *filter(None, [os.environ.get('PYTHONPATH')])])}
cwd = Pyjo.File.path()

with subtest('Synopsis'):
    application = Pyjoyment.new()
    plugin = Pyjoyment.Command.Author.generate.plugin.new(app=application)
    like_ok(
        plugin.usage, r'^Usage: APPLICATION generate plugin \[OPTIONS\] \[NAME\]\n\n  pyjo generate plugin\n', 'usage'
    )
    tmp = Pyjo.File.tempdir()
    os.chdir(tmp)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            plugin.run()
            plugin.run('AliceSearch')
            plugin.run('-f', 'MyApp.Ext.Test')
    finally:
        os.chdir(cwd)
    ok(os.path.isfile(tmp.child('Pyjoyment-Plugin-MyPlugin', 'Pyjoyment', 'Plugin', 'MyPlugin.py').to_str()), 'default')
    ok(
        os.path.isfile(tmp.child('Pyjoyment-Plugin-AliceSearch', 'Pyjoyment', 'Plugin', 'AliceSearch.py').to_str()),
        'name',
    )
    ok(os.path.isfile(tmp.child('MyApp-Ext-Test', 'MyApp', 'Ext', 'Test.py').to_str()), 'full name')

    # Not in Mojolicious: the class under the name of its module
    module = tmp.child('Pyjoyment-Plugin-MyPlugin', 'Pyjoyment', 'Plugin', 'MyPlugin.py').slurp('UTF-8')
    like_ok(module, r'\nMyPlugin = Pyjoyment_Plugin_MyPlugin\n', 'class under the name of its module')
    like_ok(tmp.child('MyApp-Ext-Test', 'MyApp', 'Ext', 'Test.py').slurp('UTF-8'), r'\nTest = MyApp_Ext_Test\n', 'full')

with subtest('Description'):
    application = Pyjoyment.new()
    plugin = Pyjoyment.Command.Author.generate.plugin.new(app=application)
    tmp = Pyjo.File.tempdir()
    os.chdir(tmp)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            plugin.run()
            plugin.run('-f', 'MyApp.Ext.Test')
    finally:
        os.chdir(cwd)
    dir = tmp.child('Pyjoyment-Plugin-MyPlugin')
    ok(not os.path.exists(dir.child('Pyjoyment', '__init__.py').to_str()), 'no __init__.py of Pyjoyment')
    ok(not os.path.exists(dir.child('Pyjoyment', 'Plugin', '__init__.py').to_str()), 'no __init__.py of the namespace')
    pyproject = tomllib.loads(dir.child('pyproject.toml').slurp().decode())
    is_ok(pyproject['build-system']['build-backend'], 'hatchling.build', 'hatchling')
    is_ok(pyproject['project']['name'], 'Pyjoyment-Plugin-MyPlugin', 'name')
    is_deeply_ok(
        pyproject['tool']['hatch']['build']['targets']['wheel']['only-include'],
        ['Pyjoyment/Plugin/MyPlugin.py'],
        'only the module',
    )
    is_deeply_ok(pyproject['tool']['pytest']['ini_options']['testpaths'], ['t'], 'testpaths of pytest')
    is_deeply_ok(pyproject['tool']['pytest']['ini_options']['pythonpath'], ['.'], 'pythonpath of pytest')
    is_deeply_ok(pyproject['dependency-groups']['dev'], ['pytest>=9', 'pytest-xdist>=3'], 'pytest in the group dev')
    for name in ('Pyjoyment-Plugin-MyPlugin', 'MyApp-Ext-Test'):
        result = subprocess.run(
            [sys.executable, '-m', 'Pyjo.Prove', '-l', '-r', 't'],
            cwd=tmp.child(name).to_str(),
            env=env,
            capture_output=True,
            text=True,
        )
        like_ok(result.stdout, r'Result: PASS', f'python -m Pyjo.Prove -l -r t of {name}')

with subtest('Attributes'):
    plugin = Pyjoyment.Command.Author.generate.plugin.new()
    is_ok(plugin.description, 'Generate Pyjoyment plugin directory structure', 'description')
    like_ok(plugin.usage, r'generate plugin', 'usage')

done_testing()
