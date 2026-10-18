"""
Invoke the emulator of the Runtime API of AWS Lambda with the event of a file,
until it answers, and check that the response is the welcome page.

Usage: python invoke.py URL EVENT.json
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request


url, path = sys.argv[1:]
name = os.path.basename(path)
with open(path, 'rb') as f:
    event = f.read()

response = None
for _ in range(60):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=event), timeout=30) as res:
            response = json.load(res)
        break
    except (urllib.error.URLError, ConnectionError):
        time.sleep(0.5)

ok = isinstance(response, dict) and response.get('statusCode') == 200 and not response.get('isBase64Encoded')
ok = ok and 'Welcome to the Pyjoyment real-time web framework!' in response.get('body', '')
if not ok:
    print(f'not ok - invoke with {name}: {response}', file=sys.stderr)
    sys.exit(1)
print(f'ok - invoke with {name}')
