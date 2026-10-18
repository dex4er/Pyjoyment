import Pyjoyment

from MyApp.Model.Users import Users


class MyApp(Pyjoyment.object):
    def startup(self):
        self.secrets = ['Pyjoyment rocks']
        users = Users()
        self.helper('users', lambda c: users)

        r = self.routes
        r.any('/', 'index').to('login#index')

        logged_in = r.under('/').to('login#logged_in')
        logged_in.get('/protected').to('login#protected')

        r.get('/logout').to('login#logout')


new = MyApp.new
object = MyApp
