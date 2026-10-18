from Pyjoyment.Lite import *


# Modify the received JSON document and return it
@put('/reverse')
def reverse(c):
    document = c.req.json()
    document['message'] = document['message'][::-1]
    c.render(json=document)


app.start()
