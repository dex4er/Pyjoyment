from Pyjoyment.Lite import *


# /foo
under('/foo')

# /foo/bar
get('/bar', {'text': 'foo bar'})

# /foo/baz
get('/baz', {'text': 'foo baz'})

# / (reset)
under('/', {'msg': 'whatever'})

# /bar
get('/bar', {'inline': '<%= msg %> works'})

app.start()
