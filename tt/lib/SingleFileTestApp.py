"""
__DATA__
@@ index.html.epl
<%= 20 + 3 %> works!
@@ too.html.epl
This one works too!
@@ singlefiletestapp/foo.txt
And this one... ALL GLORY TO THE HYPNOTOAD!
"""

import Pyjoyment
import Pyjoyment.Controller


class SingleFileTestApp(Pyjoyment.object):
    def startup(self):
        # Only log errors to STDERR
        self.log.level = 'fatal'

        # Plugins
        self.plugin('PluginWithEmbeddedApp')
        self.plugin('PyjoymentTest.Plugin.Test.SomePlugin2')
        self.plugin('Config')

        # DATA classes
        self.renderer.classes.append('SingleFileTestApp.Foo')
        self.static.classes.append('SingleFileTestApp.Foo')

        # Helper route
        self.routes.any('/helper').to(cb=lambda c: c.render(text=c.some_plugin()))

        # The default route
        r = self.routes
        r.any('/foo').to('Foo#index')
        r.any('/foo/conf').to('Foo#conf')
        r.any('/foo/data_static').to('Foo#data_static')
        r.any('/foo/data_template').to('Foo#data_template')
        r.any('/foo/data_template2').to('Foo#data_template2')
        r.any('/foo/routes').to('Foo#routes')
        r.any('/redispatch').to('Redispatch#index')
        r.any('/redispatch/render').to('Redispatch#render')
        r.any('/redispatch/secret').to('Redispatch#secret')


# Not in Mojolicious: the packages of the file of Mojo are classes of the module
class Redispatch(Pyjoyment.object):
    def handler(self, c):
        if c.param('rly'):
            return secret(c)
        if c.stash('action') == 'render':
            return render(c)
        c.render(text='Redispatch!')


def render(c):
    c.render(text='Render!')


def secret(c):
    c.render(text='Secret!')


class Foo(Pyjoyment.Controller.object):
    def conf(self):
        self.render(text=self.config()['single_file'])

    def data_template(self):
        self.render('index')

    def data_template2(self):
        self.stash(template='too')

    def data_static(self):
        self.reply.static('singlefiletestapp/foo.txt')

    def index(self):
        self.stash(template='WithGreenLayout', msg='works great!')

    def routes(self):
        self.res.headers.header('X-Bender', 'Bite my shiny metal ass!')
        self.render(text=self.url_for())


new = SingleFileTestApp.new
object = SingleFileTestApp
