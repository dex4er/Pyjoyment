"""
__DATA__

@@ foo/fun.html.ep
<p>Have fun!</p>\\

@@ foo/joy.html.ep
<p class="joy" style="background-color: darkred;" data-foo="0" data-empty="">Joy for all!</p>\\

@@ just/some/template.html.epl
Development template with high precedence.

@@ some/static/file.txt
Development static file with high precedence.
"""

import Pyjo.IOLoop
import Pyjoyment.Controller


class PyjoymentTest_Foo(Pyjoyment.Controller.object):
    def __del__(self):
        try:
            self.stash()['destroyed'] = 1
        except Exception:
            pass

    def config(self):
        self.render(text=self.stash('config')['test'])

    def fun(self):
        self.render()

    def joy(self):
        self.render()

    def index(self):
        self.layout('default')
        self.stash(handler='xpl', msg='Hello World!')

    def longpoll(self):
        @self.on('finish')
        def finish(c):
            c.stash()['finished'] = 1

        self.write_chunk(b'P', lambda c: c.write_chunk(b'oll!', lambda c: c.write_chunk(b'')))

    def plugin_camel_case(self):
        self.render(text=self.some_plugin())

    def plugin_upper_case(self):
        self.render(text=self.upper_case_test_plugin())

    def session_domain(self):
        self.session(user='Bender')
        self.render(text='Bender rockzzz!')

    def something(self):
        self.res.headers.header('X-Bender', 'Bite my shiny metal ass!')
        self.render(text=self.url_for('something', something='42'))

    def stage1(self):
        # Authenticated
        if self.req.headers.header('X-Pass'):
            return 1

        # Fail
        self.render(text='Go away!')
        return None

    def stage2(self):
        return self.some_plugin()

    def suspended(self):
        self.res.headers.append('X-Suspended', self.match.position)

        @Pyjo.IOLoop.next_tick
        def next_tick(loop):
            self.res.headers.append('X-Suspended', self.match.position)
            self.continue_()

        return 0

    def syntaxerror(self):
        self.render('syntaxerror', format='html')

    def templateless(self):
        self.render(handler='test')

    def test(self):
        self.res.headers.header('X-Bender', 'Bite my shiny metal ass!')
        self.render(text=self.url_for(foo='bar'))

    def url_for_missing(self):
        self.render(text=self.url_for('does_not_exist', something='42'))

    def willdie(self):
        raise Exception('for some reason')

    def withBlock(self):
        self.render(template='withblock')

    def withlayout(self):
        self.stash(template='WithGreenLayout')


object = PyjoymentTest_Foo
