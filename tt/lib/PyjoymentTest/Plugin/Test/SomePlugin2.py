import Pyjoyment.Plugin


class PyjoymentTest_Plugin_Test_SomePlugin2(Pyjoyment.Plugin.object):
    def register(self, app, conf=None):
        # Add "some_plugin" helper
        app.helper('some_plugin', lambda c: 'Welcome aboard!')


object = PyjoymentTest_Plugin_Test_SomePlugin2
