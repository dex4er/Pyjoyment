async def app(scope, receive, send):
    if scope['type'] != 'http':
        return
    await send(
        {
            'type': 'http.response.start',
            'status': 200,
            'headers': [(b'content-type', b'text/html;charset=UTF-8'), (b'content-length', b'21')],
        }
    )
    await send({'type': 'http.response.body', 'body': b'Your Pyjo is working!'})
