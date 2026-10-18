import Pyjoyment.Plugin


class MyApp_Plugin_MyHelpers(Pyjoyment.Plugin.object):
    def register(self, app, conf):
        @app.helper('my_helpers.render_with_header')
        def render_with_header(c, *args, **kwargs):
            c.res.headers.header('X-Pyjo', 'I <3 Pyjoyment!')
            c.render(*args, **kwargs)


object = MyApp_Plugin_MyHelpers
