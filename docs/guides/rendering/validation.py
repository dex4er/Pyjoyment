"""
__DATA__

@@ index.html.ep
<!DOCTYPE html>
<html>
  <head>
    <style>
      label.field-with-error { color: #dd7e5e }
      input.field-with-error { background-color: #fd9e7e }
    </style>
  </head>
  <body>
    %= form_for('index', begin
      %= label_for('user', 'Username (required, 1-20 characters, a-z/0-9)')
      <br>
      %= text_field('user', id='user')
      %= submit_button()
      <br>
      %= label_for('pass', 'Password (optional, 7-500 characters)')
      <br>
      %= password_field('pass', id='pass')
      <br>
      %= label_for('pass_again', 'Password again (equal to the value above)')
      <br>
      %= password_field('pass_again', id='pass_again')
    % end)
  </body>
</html>

@@ thanks.html.ep
<!DOCTYPE html>
<html><body>Thank you <%= validation().param('user') %>.</body></html>
"""

from Pyjoyment.Lite import *

import re


@get('/', 'index')
def index(c):

    # Check if parameters have been submitted
    v = c.validation()
    if not v.has_data:
        return c.render('index')

    # Validate parameters ("pass_again" depends on "pass")
    v.required('user').size(1, 20).like(re.compile(r'^[a-z0-9]+$'))
    if v.optional('pass').size(7, 500).is_valid():
        v.required('pass_again').equal_to('pass')

    # Check if validation failed
    if v.has_error():
        return c.render('index')

    # Render confirmation
    c.render('thanks')


app.start()
