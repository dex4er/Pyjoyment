"""
__DATA__

@@ alertassets.js
alert("Hello World!");

@@ alertassets.html.ep
%= javascript("/alertassets.js")
"""

import Pyjoyment.Plugin


class Pyjoyment_Plugin_AlertAssets(Pyjoyment.Plugin.object):
    def register(self, app, conf):

        # Append class
        app.renderer.classes.append(__name__)
        app.static.classes.append(__name__)


object = Pyjoyment_Plugin_AlertAssets
