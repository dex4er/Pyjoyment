import Pyjoyment.Controller


class MyApp_Controller_Login(Pyjoyment.Controller.object):
    def index(self):
        user = self.param('user') or ''
        password = self.param('pass') or ''
        if not self.users().check(user, password):
            return self.render()

        self.session(user=user)
        self.flash(message='Thanks for logging in.')
        self.redirect_to('protected')

    def logged_in(self):
        if self.session('user'):
            return True
        self.redirect_to('index')
        return None

    def logout(self):
        self.session(expires=1)
        self.redirect_to('index')


object = MyApp_Controller_Login
