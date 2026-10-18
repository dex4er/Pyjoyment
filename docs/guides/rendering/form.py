"""
__DATA__

@@ form.html.ep
<!DOCTYPE html>
<html>
  <body>
    % if (confirmation := flash('confirmation')):
      <p><%= confirmation %></p>
    % end
    %= form_for('nothing', begin
      %= text_field('whatever', 'I ♥ Pyjoyment!')
      %= submit_button()
    % end)
  </body>
</html>
"""

from Pyjoyment.Lite import *


get('/', 'form')


# PUT  /nothing
# POST /nothing?_method=PUT
@put('/nothing')
def nothing(c):

    # Prevent double form submission with redirect
    value = c.param('whatever')
    c.flash(confirmation=f'We did nothing with your value ({value}).')
    c.redirect_to('form')


app.start()
