"""
__DATA__

@@ index.html.ep
<!DOCTYPE html>
<html>
  <head><title>Streaming multipart upload</title></head>
  <body>
    %= form_for('upload', begin
      %= file_field('example')
      %= submit_button('Upload')
    % end, enctype='multipart/form-data')
  </body>
</html>
"""

from Pyjoyment.Lite import *

import weakref


# Intercept multipart uploads and log each chunk received
@hook('after_build_tx')
def after_build_tx(tx, app):
    # Subscribe to "upgrade" event to identify multipart uploads
    tx = weakref.proxy(tx)

    @tx.req.content.on('upgrade')
    def upgrade(single, multi):
        if not tx.req.url.path.contains('/upload'):
            return

        # Subscribe to "part" event to find the right one
        @multi.on('part')
        def part(multi, single):
            # Subscribe to "body" event of part to make sure we have all headers
            @single.on('body')
            def body(single):
                # Make sure we have the right part and replace "read" event
                if 'example' not in (single.headers.content_disposition or ''):
                    return

                # Log size of every chunk we receive
                single.unsubscribe('read').on('read', lambda single, data: app.log.debug(f'{len(data)} bytes uploaded'))


# Upload form in DATA section
get('/', 'index')

# Streaming multipart upload
post('/upload', {'text': 'Upload was successful.'})

app.start()
