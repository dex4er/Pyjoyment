# On an ASGI server: uvicorn hello_asgi:app
async def app(scope, receive, send):
    if scope['type'] != 'http':
        return

    # Server-sent events, each sent once the one before has been written
    if scope['path'].endswith('/events'):
        await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/event-stream')]})
        for n in range(3):
            await send({'type': 'http.response.body', 'body': f'data: {n}\n\n'.encode(), 'more_body': True})
        await send({'type': 'http.response.body', 'body': b''})
        return

    body = f'Hello ASGI at {scope["root_path"]} for {scope["path"]}!'.encode()
    await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'content-type', b'text/plain')]})
    await send({'type': 'http.response.body', 'body': body})
