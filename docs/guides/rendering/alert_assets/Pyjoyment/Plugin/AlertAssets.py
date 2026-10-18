import Pyjoyment.Plugin

from Pyjo.File import curfile


class Pyjoyment_Plugin_AlertAssets(Pyjoyment.Plugin.object):
    def register(self, app, conf):

        # Append "templates" and "public" directories
        base = curfile().sibling('AlertAssets')
        app.renderer.paths.append(base.child('templates').to_str())
        app.static.paths.append(base.child('public').to_str())


object = Pyjoyment_Plugin_AlertAssets
