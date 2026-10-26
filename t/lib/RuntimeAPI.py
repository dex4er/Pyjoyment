import Pyjo.IOLoop
import Pyjo.Server.Daemon
import Pyjoyment

import os
import subprocess
import time


# The checkout, whose modules the runtime client imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


# A Runtime API of AWS Lambda, which gives the events one after another, with the headers of an invocation, and keeps
# what the runtime client of the command posts, which runs in a process of its own until the posts are there, and to
# its end, when it ends by itself
def invoke(command, events, posts, cwd, env=None, ends=False):
    api = Pyjoyment.new()
    api.log.level = 'fatal'
    queue = list(events)
    got = []

    @api.routes.get('/2018-06-01/runtime/invocation/next')
    def next_(c):
        if not queue:
            return c.render_later()
        id, event = queue.pop(0)
        headers = c.res.headers
        headers.header('Lambda-Runtime-Aws-Request-Id', id)
        headers.header('Lambda-Runtime-Deadline-Ms', str(int((time.time() + 60) * 1000)))
        headers.header('Lambda-Runtime-Invoked-Function-Arn', 'arn:aws:lambda:eu-central-1:123456789012:function:test')
        headers.header('Lambda-Runtime-Trace-Id', f'Root=1-{id}')
        c.render(json=event)

    # The chunks of a request with the times they come at
    reads = {}

    @api.hook('after_build_tx')
    def build(tx, app):
        chunks = reads[id(tx.req)] = []
        tx.req.content.on('read', lambda content, chunk: chunks.append((time.time(), bytes(chunk))))

    # A streaming response as its content type, its body, its chunks and the body of the error in its trailers, which
    # are headers of the request once it is parsed, and another response as JSON
    def post(kind):
        def action(c):
            headers = c.req.headers
            chunks = reads.pop(id(c.req), [])
            if headers.header('Lambda-Runtime-Function-Response-Mode') == 'streaming':
                body = {
                    'content_type': headers.content_type,
                    'body': c.req.body,
                    'chunks': chunks,
                    'error_body': headers.header('Lambda-Runtime-Function-Error-Body'),
                }
            else:
                body = c.req.json()
            got.append((kind, c.param('id'), headers.header('Lambda-Runtime-Function-Error-Type'), body))
            c.render(data=b'', status=202)

        return action

    api.routes.post('/2018-06-01/runtime/invocation/<id>/response').to(cb=post('response'))
    api.routes.post('/2018-06-01/runtime/invocation/<id>/error').to(cb=post('error'))
    api.routes.post('/2018-06-01/runtime/init/error').to(cb=post('init'))
    daemon = Pyjo.Server.Daemon.new(app=api, listen=['http://127.0.0.1'], silent=True).start()
    environ = {
        **os.environ,
        'PYTHONPATH': os.pathsep.join([ROOT, *filter(None, [os.environ.get('PYTHONPATH')])]),
        'AWS_LAMBDA_RUNTIME_API': f'127.0.0.1:{daemon.ports()[0]}',
        'AWS_LAMBDA_FUNCTION_NAME': 'test',
        'AWS_LAMBDA_FUNCTION_MEMORY_SIZE': '128',
        **(env or {}),
    }
    process = subprocess.Popen(command, cwd=cwd, env=environ)
    try:
        # Until the posts, which the event loop answers in the meantime, and the end of a process that ends by itself, a
        # process that ends before them, or a timeout
        def ended(loop):
            if process.poll() is not None or len(got) >= posts and not ends:
                loop.stop()

        waiting = [Pyjo.IOLoop.recurring(0.05, ended), Pyjo.IOLoop.timer(30, lambda loop: loop.stop())]
        Pyjo.IOLoop.start()
        for timer in waiting:
            Pyjo.IOLoop.remove(timer)
    finally:
        if not ends:
            process.terminate()
        code = process.wait(10)
        daemon.close()
    return got, code


if __name__ == '__main__':
    from Pyjo.Test import plan

    plan(skip_all='helper module, not a test')
