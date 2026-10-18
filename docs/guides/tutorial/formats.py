"""
__DATA__

@@ detected.html.ep
<!DOCTYPE html>
<html>
  <head><title>Detected</title></head>
  <body>HTML was detected.</body>
</html>

@@ detected.txt.ep
TXT was detected.
"""

from Pyjoyment.Lite import *


# /detection.html
# /detection.txt
@get('/detection', format=['html', 'txt'])
def detection(c):
    c.render(template='detected')


app.start()
