import json


# An ASGI application, as an application of Starlette is one, with server-sent events
async def app(scope, receive, send):
    if scope['path'] == f'{scope["root_path"]}/events':
        await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/event-stream')]})
        for n in range(3):
            await send({'type': 'http.response.body', 'body': f'data: {n}\n\n'.encode(), 'more_body': True})
        await send({'type': 'http.response.body', 'body': b''})
        return

    body = json.dumps({'root_path': scope['root_path'], 'path': scope['path']}).encode()
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'application/json')]})
    await send({'type': 'http.response.body', 'body': body})
