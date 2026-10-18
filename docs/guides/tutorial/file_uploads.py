"""
__DATA__

@@ form.html.ep
<!DOCTYPE html>
<html>
  <head><title>Upload</title></head>
  <body>
    %= form_for('upload', begin
      %= file_field('example')
      %= submit_button('Upload')
    % end, enctype='multipart/form-data')
  </body>
</html>
"""

from Pyjoyment.Lite import *


# Upload form in DATA section
get('/', 'form')


# Multipart upload handler
@post('/upload')
def upload(c):

    # Check file size
    if c.req.is_limit_exceeded:
        return c.render(text='File is too big.', status=200)

    # Process uploaded file
    if not (example := c.param('example')):
        return c.redirect_to('form')
    size = example.size
    name = example.filename
    c.render(text=f'Thanks for uploading {size} byte file {name}.')


app.start()
