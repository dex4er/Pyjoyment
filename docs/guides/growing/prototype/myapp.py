#!/usr/bin/env python
"""
__DATA__

@@ index.html.ep
% layout('default')
%= form_for('index', begin
  % if param('user'):
    <b>Wrong name or password, please try again.</b><br>
  % end
  Name:<br>
  %= text_field('user')
  <br>Password:<br>
  %= password_field('pass')
  <br>
  %= submit_button('Login')
% end)

@@ protected.html.ep
% layout('default')
% if (msg := flash('message')):
  <b><%= msg %></b><br>
% end
Welcome <%= session('user') %>.<br>
%= link_to('Logout', 'logout')

@@ layouts/default.html.ep
<!DOCTYPE html>
<html>
  <head><title>Login Manager</title></head>
  <body><%= content() %></body>
</html>
"""

from Pyjoyment.Lite import *

from MyApp.Model.Users import Users


# Make signed cookies tamper resistant
app.secrets = ['Pyjoyment rocks']

users = Users()
helper('users', lambda c: users)


# Main login action
@any('/', 'index')
def index(c):

    # Query or POST parameters
    user = c.param('user') or ''
    password = c.param('pass') or ''

    # Check password and render "index.html.ep" if necessary
    if not c.users().check(user, password):
        return c.render()

    # Store username in session
    c.session(user=user)

    # Store a friendly message for the next page in flash
    c.flash(message='Thanks for logging in.')

    # Redirect to protected page with a 302 response
    c.redirect_to('protected')


# Make sure user is logged in for actions in this group
with group():

    @under
    def logged_in(c):

        # Redirect to main page with a 302 response if user is not logged in
        if c.session('user'):
            return True
        c.redirect_to('index')
        return None

    # A protected page auto rendering "protected.html.ep"
    get('/protected')


# Logout action
@get('/logout')
def logout(c):

    # Expire and in turn clear session automatically
    c.session(expires=1)

    # Redirect to main page with a 302 response
    c.redirect_to('index')


app.start()
