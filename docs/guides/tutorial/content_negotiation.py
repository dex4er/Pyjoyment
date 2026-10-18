from Pyjoyment.Lite import *


# /hello (Accept: application/json)
# /hello (Accept: application/xml)
# /hello.json
# /hello.xml
# /hello?_format=json
# /hello?_format=xml
@get('/hello', {'format': None}, format=['json', 'xml'])
def hello(c):
    c.respond_to(
        json={'json': {'hello': 'world'}},
        xml={'text': '<hello>world</hello>'},
        any={'data': b'', 'status': 204},
    )


app.start()
