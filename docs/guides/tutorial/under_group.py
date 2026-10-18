from Pyjoyment.Lite import *


# Global logic shared by all routes
@under
def bender(c):
    if c.req.headers.header('X-Bender'):
        return True
    c.render(text="You're not Bender.")
    return None


# Admin section
with group():
    # Local logic shared only by routes in this group
    @under('/admin')
    def admin(c):
        if c.req.headers.header('X-Awesome'):
            return True
        c.render(text="You're not awesome enough.")
        return None

    # GET /admin/dashboard
    get('/dashboard', {'text': 'Nothing to see here yet.'})

# GET /welcome
get('/welcome', {'text': 'Hi Bender.'})

app.start()
