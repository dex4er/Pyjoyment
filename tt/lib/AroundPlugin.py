import Pyjoyment.Plugin


class AroundPlugin(Pyjoyment.Plugin.object):
    def register(self, app, conf=None):
        # Render return value
        @app.hook('around_action')
        def around_action(next, c, action, last):
            value = next()
            if last and c.stash().get('return'):
                c.render(text=value)
            return value


object = AroundPlugin
