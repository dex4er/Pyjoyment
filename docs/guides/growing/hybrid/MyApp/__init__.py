import Pyjoyment

from MyApp.Model.Users import Users


class MyApp(Pyjoyment.object):
    def startup(self):

        self.secrets = ['Pyjoyment rocks']
        users = Users()
        self.helper('users', lambda c: users)

        r = self.routes

        @r.any('/', 'index')
        def index(c):

            user = c.param('user') or ''
            password = c.param('pass') or ''
            if not c.users().check(user, password):
                return c.render()

            c.session(user=user)
            c.flash(message='Thanks for logging in.')
            c.redirect_to('protected')

        @r.under
        def logged_in(c):
            if c.session('user'):
                return True
            c.redirect_to('index')
            return None

        logged_in.get('/protected')

        @r.get('/logout')
        def logout(c):
            c.session(expires=1)
            c.redirect_to('index')


new = MyApp.new
object = MyApp
