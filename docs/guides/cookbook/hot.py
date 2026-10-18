from Pyjoyment.Lite import *


app.config(hot={'listen': ['http://*:80']})

get('/', {'text': 'Hello World!'})

app.start()
