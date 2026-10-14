import asyncio


# An ASGI server for the tests: it calls the application with a scope and messages of its own, and collects the
# messages that the application sends, as uvicorn would do for one connection
def http(method='GET', path='/', query=b'', body=b'', headers=(), chunks=1, **scope):
    pieces = [body[i * len(body) // chunks : (i + 1) * len(body) // chunks] for i in range(chunks)] or [b'']
    messages = [{'type': 'http.request', 'body': p, 'more_body': i < len(pieces) - 1} for i, p in enumerate(pieces)]
    return {
        'type': 'http',
        'asgi': {'version': '3.0'},
        'http_version': '1.1',
        'method': method,
        'scheme': 'http',
        'path': path,
        'raw_path': path.encode(),
        'query_string': query,
        'root_path': '',
        'headers': [(b'host', b'localhost:8000'), *headers],
        'client': ('127.0.0.1', 50000),
        'server': ('127.0.0.1', 8000),
        **scope,
    }, messages


def websocket(path='/', messages=(), headers=(), **scope):
    return {
        'type': 'websocket',
        'asgi': {'version': '3.0'},
        'http_version': '1.1',
        'scheme': 'ws',
        'path': path,
        'raw_path': path.encode(),
        'query_string': b'',
        'root_path': '',
        'headers': [
            (b'host', b'localhost:8000'),
            (b'upgrade', b'websocket'),
            (b'connection', b'Upgrade'),
            (b'sec-websocket-key', b'dGhlIHNhbXBsZSBub25jZQ=='),
            (b'sec-websocket-version', b'13'),
            *headers,
        ],
        'client': ('127.0.0.1', 50000),
        'server': ('127.0.0.1', 8000),
        'subprotocols': [],
        **scope,
    }, [{'type': 'websocket.connect'}, *messages]


async def call(app, scope, messages):
    queue = list(messages)
    sent = []

    async def receive():
        # Like a real server, a message arrives in a later iteration of the event loop
        await asyncio.sleep(0.01)
        if queue:
            return queue.pop(0)
        await asyncio.Event().wait()

    async def send(message):
        sent.append(message)

    await asyncio.wait_for(app(scope, receive, send), 10)
    return sent


def run(app, scope, messages):
    return asyncio.run(call(app, scope, messages))


def response(sent):
    start = next(m for m in sent if m['type'] == 'http.response.start')
    headers = {name.decode(): value.decode() for name, value in start['headers']}
    body = b''.join(m.get('body', b'') for m in sent if m['type'] == 'http.response.body')
    return start['status'], headers, body


if __name__ == '__main__':
    from Pyjo.Test import plan

    plan(skip_all='helper module, not a test')
