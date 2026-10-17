import Pyjoyment


class MyApp(Pyjoyment.object):
    def startup(self):
        r = self.routes

        self.plugin('Config')

        r.get('/', lambda self: self.render(text=self.config()['works']))

        r.get('/test', lambda self: self.render(text=self.config()['whatever']))

        def secondary(self):
            session = self.session()
            session['secondary'] = session.get('secondary', 0) + 1
            self.render(text=str(session['secondary']))

        r.get('/secondary', secondary)

        r.get('/inline', lambda self: self.render(inline="<%= config()['whatever'] =%>"))


new = MyApp.new
object = MyApp
