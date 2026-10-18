from Pyjoyment.Lite import *


@helper('cache_control.no_caching')
def no_caching(c):
    c.res.headers.cache_control = 'private, max-age=0, no-cache'


@helper('cache_control.five_minutes')
def five_minutes(c):
    c.res.headers.cache_control = 'public, max-age=300'


@get('/news')
def news(c):
    c.cache_control.no_caching()
    c.render(text='Always up to date.')


@get('/some_older_story')
def some_older_story(c):
    c.cache_control.five_minutes()
    c.render(text='This one can be cached for a bit.')


app.start()
