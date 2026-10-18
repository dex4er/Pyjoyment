import Pyjoyment.Plugin


class Pyjoyment_Plugin_DebugHelper(Pyjoyment.Plugin.object):
    def register(self, app, conf):
        @app.helper('debug')
        def debug(c, string):
            c.app.log.debug(string)


object = Pyjoyment_Plugin_DebugHelper
