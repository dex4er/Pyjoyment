"""
__DATA__

@@ index.html.ep
<!DOCTYPE html>
<html>
  <head><title>LiveLog</title></head>
  <body>
    <script>
      const events = new EventSource('<%= url_for('events') %>');

      // Subscribe to "log" event
      events.addEventListener('log', function (event) {
        document.body.innerHTML += event.data + '<br/>';
      }, false);
    </script>
  </body>
</html>
"""

from Pyjoyment.Lite import *


# Template with browser-side code
get('/', 'index')


# EventSource for log messages
@get('/events')
def events(c):
    # Increase inactivity timeout for connection a bit
    c.inactivity_timeout(300)

    # Change content type and finalize response headers
    c.write_sse()

    # Subscribe to "message" event and forward "log" events to browser
    @c.app.log.on('message')
    def message(log, level, *lines):
        c.write_sse({'type': 'log', 'text': f'[{level}] {" ".join(lines)}'})

    # Unsubscribe from "message" event again once we are done
    c.on('finish', lambda c: c.app.log.unsubscribe('message', message))


app.start()
