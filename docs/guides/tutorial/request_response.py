from Pyjoyment.Lite import *


# Access request information
@get('/agent')
def agent(c):
    host = c.req.url.to_abs().host
    ua = c.req.headers.user_agent
    c.render(text=f'Request by {ua} reached {host}.')


# Echo the request body and send custom header with response
@post('/echo')
def echo(c):
    c.res.headers.header('X-Bender', 'Bite my shiny metal ass!')
    c.render(data=c.req.body)


app.start()
