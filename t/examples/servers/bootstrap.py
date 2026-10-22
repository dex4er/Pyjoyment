import Pyjo.File

from Pyjo.Test import *

import importlib
import os
import sys


# The bootstrap of the example, with the handler of hello_world_lambda.py, for an invocation of a Runtime API of the
# test, with the Python of the test as python3
if sys.platform == 'win32':
    plan(skip_all='no shell of POSIX on Windows')

sys.path.insert(0, Pyjo.File.curfile().dirname().dirname().sibling('lib').to_str())
RuntimeAPI = importlib.import_module('RuntimeAPI')
servers = Pyjo.File.curfile().dirname().dirname().dirname().sibling('examples', 'servers')
bin = Pyjo.File.tempdir()
os.symlink(sys.executable, bin.child('python3').to_str())

with subtest('Function URL'):
    event = {
        'version': '2.0',
        'rawPath': '/',
        'rawQueryString': '',
        'headers': {'host': 'abc.lambda-url.eu-central-1.on.aws'},
        'requestContext': {'http': {'method': 'GET'}, 'stage': '$default'},
        'isBase64Encoded': False,
    }
    env = {
        '_HANDLER': 'hello_world_lambda.handler',
        'LAMBDA_TASK_ROOT': servers.to_str(),
        'PATH': os.pathsep.join([bin.to_str(), os.environ.get('PATH', '')]),
    }
    got, code = RuntimeAPI.invoke(['sh', servers.child('bootstrap').to_str()], [('a1', event)], 1, bin.to_str(), env)
    is_ok(got[0][:2], ('response', 'a1'), 'response of the invocation')
    is_ok(got[0][3]['statusCode'], 200, 'status')
    is_ok(got[0][3]['body'], 'Your Pyjo is working!', 'body')

done_testing()
