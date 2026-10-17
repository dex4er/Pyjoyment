import Pyjoyment.Plugin


class PyjoymentTest_Plugin_DeploymentPlugin(Pyjoyment.Plugin.object):
    def register(self, app, config=None):
        config = config or {}
        name = config.get('name', 'deployment_helper')
        msg = config.get('message', 'deployment plugins work!')
        app.helper(name, lambda c: msg)


object = PyjoymentTest_Plugin_DeploymentPlugin
