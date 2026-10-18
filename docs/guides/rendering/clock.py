"""
__DATA__

@@ clock.html.ep
% import time
% now = time.localtime()
<!DOCTYPE html>
<html>
  <head><title>Time</title></head>
  <body>The time is <%= time.strftime('%H:%M:%S', now) %>.</body>
</html>

@@ hello.txt.ep
Hello <%= name %>.
"""

from Pyjoyment.Lite import *


get('/clock')
get('/hello', {'format': 'txt', 'name': 'World'})

app.start()
