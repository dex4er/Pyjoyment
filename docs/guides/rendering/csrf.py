"""
__DATA__

@@ target.html.ep
<!DOCTYPE html>
<html>
  <body>
    %= form_for('target', begin
      %= csrf_field()
      %= label_for('city', 'Which city to point low orbit ion cannon at?')
      %= text_field('city', id='city')
      %= submit_button()
    %= end)
  </body>
</html>
"""

from Pyjoyment.Lite import *


get('/', {'template': 'target'})


@post('/', 'target')
def target(c):

    # Check CSRF token
    v = c.validation()
    if v.csrf_protect().has_error('csrf_token'):
        return c.render(text='Bad CSRF token!', status=403)

    city = v.required('city').param('city')
    if not v.has_error():
        c.render(text=f'Low orbit ion cannon pointed at {city}!')


app.start()
