import Pyjo.App.Lambda
import Pyjo.Test.Pyjo

from Pyjo.File import curfile
from Pyjo.Test import *

import os
import platform
import sys


# The function of examples/lambda_zip on AWS, behind the Function URL of TEST_LAMBDA_ZIP_URL, which "tofu output -raw
# url" gives, or with Pyjo.App.Lambda otherwise, which runs the script as the runtime of the function, as its bootstrap
# does
ROOT = curfile().dirname().dirname().dirname()
URL = os.environ.get('TEST_LAMBDA_ZIP_URL')

if not URL and os.name == 'nt':
    plan(skip_all='Lambda functions need pipes that the event loop watches, which Windows does not have')


def check(t: Pyjo.Test.Pyjo.object, url: str) -> None:
    with subtest('Hello'):
        t.get_ok(f'{url}/').status_is(200).content_is('Hello Pyjoyment on AWS Lambda, from a ZIP file!')

    with subtest('Python'):
        t.get_ok(f'{url}/python').status_is(200).json_has('/version').json_has('/free_threaded')
        if URL:
            # The Python of the layer, with the certificates of Amazon Linux
            like_ok(t.tx.res.json('/executable'), r'^/opt/python/bin/python3\.\d+t?$', 'Python of the layer')
            ok((t.tx.res.json('/certificates') or 0) > 0, 'certificates of the system')
        else:
            t.json_is('/version', platform.python_version()).json_is('/executable', sys.executable)

    with subtest('Not found'):
        t.get_ok(f'{url}/missing').status_is(404)


if URL:
    with subtest('Function URL on AWS'):
        check(Pyjo.Test.Pyjo.new(), URL.rstrip('/'))
else:
    task_root = ROOT.sibling('examples', 'lambda_zip', 'function').to_str()
    for mode in ('BUFFERED', 'RESPONSE_STREAM'):
        with subtest(f'Function URL, {mode}'):
            env = {'PYJO_MODE': 'production', 'PYJO_LAMBDA_INVOKE_MODE': mode, 'PYTHONPATH': ROOT.dirname().to_str()}
            command = [sys.executable, 'app.py']
            with Pyjo.App.Lambda.new(command=command, task_root=task_root, env=env) as function:
                check(Pyjo.Test.Pyjo.new(function), '')

done_testing()
