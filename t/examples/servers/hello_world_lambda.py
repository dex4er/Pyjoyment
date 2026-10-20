import Pyjo.File

from Pyjo.Test import *

import runpy


# The example itself, as it needs no network and no library of its own
script = (
    Pyjo.File.curfile().dirname().dirname().dirname().sibling('examples', 'servers', 'hello_world_lambda.py').to_str()
)
handler = runpy.run_path(script)['handler']

with subtest('Function URL'):
    response = handler(
        {
            'version': '2.0',
            'rawPath': '/',
            'rawQueryString': '',
            'headers': {'host': 'abc.lambda-url.eu-central-1.on.aws'},
            'requestContext': {'http': {'method': 'GET'}, 'stage': '$default'},
            'isBase64Encoded': False,
        },
        None,
    )
    is_ok(response['statusCode'], 200, 'status')
    is_ok(response['body'], 'Your Pyjo is working!', 'body')

done_testing()
