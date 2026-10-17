import Pyjoyment.Plugin


class PyjoymentTest_Plugin_UPPERCASETestPlugin(Pyjoyment.Plugin.object):
    def register(self, app, conf=None):
        # Add "upper_case_test_plugin" helper
        app.helper('upper_case_test_plugin', lambda c: 'WELCOME aboard!')


object = PyjoymentTest_Plugin_UPPERCASETestPlugin
