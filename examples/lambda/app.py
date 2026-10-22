from Pyjoyment.Lite import *


@get('/')
def index(c):
    c.render(text='Hello Pyjoyment on AWS Lambda!')


# What the function gets of a request, after the load balancer and the event
@any('/echo')
def echo(c):
    req = c.req
    c.render(
        json={
            'method': req.method,
            'path': req.url.path.to_str(),
            'query': req.query_params.to_dict(),
            'body': req.text,
        }
    )


# The handler "app.handler" of the event function, and the command of the arguments otherwise
handler = app.start()
