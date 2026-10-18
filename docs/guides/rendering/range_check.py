"""
__DATA__

@@ form.html.ep
<!DOCTYPE html>
<html>
  <body>
    % if (number := flash('number')):
      <p>Thanks, the number <%= number %> was valid.</p>
    % end
    %= form_for('test', begin
      % if (err := validation().error('number')):
        <p>
          % if err[0] == 'required':
          Value is required.
          % end
          % if err[0] == 'range':
          Value needs to be between 3 and 23.
          % end
        </p>
      % end
      %= text_field('number')
      %= submit_button()
    % end)
  </body>
</html>
"""

from Pyjoyment.Lite import *


# Add "range" check
@app.validator.add_check('range')
def range_check(v, name, value, min, max):
    return float(value) < min or float(value) > max


get('/', 'form')


@post('/test')
def test(c):

    # Validate parameters with custom check
    v = c.validation()
    v.required('number').range(3, 23)

    # Render form again if validation failed
    if v.has_error():
        return c.render('form')

    # Prevent double form submission with redirect
    c.flash(number=v.param('number'))
    c.redirect_to('form')


app.start()
