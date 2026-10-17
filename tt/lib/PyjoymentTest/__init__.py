"""
__DATA__

@@ some/static/file.txt
Production static file with low precedence.

@@ just/some/template.html.ep
Production template with low precedence.
"""

import Pyjoyment
import PyjoymentTest.Foo  # noqa: F401


class PyjoymentTest(Pyjoyment.object):
    def startup(self):
        if self.mode == 'development':
            # Template and static file class with higher precedence for development
            self.static.classes.insert(0, 'PyjoymentTest.Foo')
            self.renderer.classes.insert(0, 'PyjoymentTest.Foo')

            # Static root for development
            self.static.paths.insert(0, self.home.child('public_dev').to_str())

            # Development namespace
            self.routes.namespaces.insert(0, 'PyjoymentTest3')

        # Template and static file class with lower precedence for production
        self.static.classes.append('PyjoymentTest')
        self.renderer.classes.append('PyjoymentTest')

        # Application specific commands
        self.commands.namespaces.append('PyjoymentTest.Command')

        # Plugins in custom namespace
        self.plugins.namespaces.insert(0, self.routes.namespaces[-1] + '.Plugin')
        self.plugin('test-some_plugin2')
        self.plugin('UPPERCASETestPlugin')

        # Plugin for rendering return values
        self.plugin('AroundPlugin')

        # Templateless renderer
        def test(renderer, c, output, options):
            output.write('Hello Mojo from a templateless renderer!')

        self.renderer.add_handler('test', test)

        # Renderer for a different file extension
        self.renderer.add_handler('xpl', self.renderer.handlers['epl'])

        # Shortcut for "/fun*" routes
        self.routes.add_shortcut('fun', lambda r, append: r.any(f'/fun{append}'))

        # Session
        self.sessions.cookie_domain = '.example.com'
        self.sessions.cookie_path = '/bar'

        # /plugin/upper_case
        # /plugin/camel_case (plugins loaded correctly)
        r = self.routes
        r.any('/plugin/upper_case').to('foo#plugin_upper_case')
        r.any('/plugin/camel_case').to('foo#plugin_camel_case')

        # /exceptional/*
        r.any('/exceptional/this_one_dies').to('exceptional#this_one_dies')

        # /exceptional_too/*
        (
            r.any('/exceptional_too')
            .set(inline=True)
            .to('exceptional#this_one_might_die')
            .any('/this_one_dies')
            .to('#this_one_dies')
        )

        # /fun/time
        r.fun('/time').to('foo#fun')

        # /happy/fun/time
        r.any('/happy').fun('/time').to('foo#fun')

        # /fun/joy
        r.fun('/joy').to('foo#joy')

        # /stash_config
        r.any('/stash_config').to(controller='foo', action='config', config={'test': 123})

        # /test4 (named route for url_for)
        r.any('/test4/:something').to('foo#something', something=23).name = 'something'

        # /somethingtest (refer to another route with url_for)
        r.put('/somethingtest').to('foo#something')

        # /something_missing (refer to a non-existing route with url_for)
        r.any('/something_missing').to('foo#url_for_missing')

        # /test3 (no class, just a namespace)
        r.any('/test3').to(namespace='PyjoymentTest2.Foo', action='test')

        # /test4 (controller class without action)
        r.any('/test1').to(controller='Foo.Bar')

        # /test2 (different namespace test)
        r.any('/test2').to(namespace='PyjoymentTest2', controller='Foo', action='test')

        # /test6 (no namespace test)
        r.any('/test6').to(namespace='', controller='pyjoyment_test2-foo', action='test')

        # /test7 (controller class shortcut)
        r.any('/test7').to('Foo.Bar#test')

        # /test8 (controller class)
        r.any('/test8').to(controller='Foo.Bar', action='test')

        # /test9 (controller in development namespace)
        r.any('/test9').to('bar#index')

        # /test10 (controller in both namespaces)
        r.any('/test10').to('baz#index')

        # /withblock (template with blocks)
        r.any('/withblock', format=['txt']).to('foo#withBlock')

        # /staged (authentication with intermediate destination)
        b = r.any('/staged').set(inline=True).to('foo#stage1', **{'return': 1})
        b.any().to(action='stage2')

        # /suspended (suspended intermediate destination)
        (
            r.any('/suspended')
            .set(inline=True)
            .to('foo#suspended')
            .any()
            .set(inline=True)
            .to('foo#suspended')
            .any()
            .to('foo#fun')
        )

        # /longpoll (long polling)
        r.any('/longpoll').to('foo#longpoll')

        # /shortcut/act
        # /shortcut/ctrl
        # /shortcut/ctrl-act (shortcuts to controller#action)
        r.any('/shortcut/ctrl-act').to('foo#config', config={'test': 'ctrl-act'})
        r.any('/shortcut/ctrl').to('foo#', action='config', config={'test': 'ctrl'})
        r.any('/shortcut/act').to('#config', controller='foo', config={'test': 'act'})

        # /foo/session (session cookie with domain)
        r.any('/foo/session').to('foo#session_domain')

        # /rss.xml (mixed formats)
        r.any('/rss.xml').to('foo#bar', format='rss')

        r.any('/foo/yada').to('Foo#yada')
        r.any('/foo').to('foo#index')
        r.any('/foo-bar').to('foo-bar#index')
        r.any('/foo/baz').to('foo#baz')
        r.any('/plugin-test-some_plugin2/register').to('plugin-test-some_plugin2#register')
        r.any('/foo/syntaxerror').to('foo#syntaxerror')
        r.any('/syntax_error/foo').to('syntax_error#foo')
        r.any('/:foo/test', foo=['foo', 'bar']).to('foo#test')
        r.any('/another').to('another#index')
        r.any('/foo/willdie').to('foo#willdie')
        r.any('/foo/templateless').to('foo#templateless')
        r.any('/foo/withlayout').to('foo#withlayout')
        r.any('/side_effects-test/index').to('side_effects-test#index')

        # /just/some/template (embedded template)
        r.any('/just/some/template').to(template='just/some/template')


new = PyjoymentTest.new
object = PyjoymentTest
