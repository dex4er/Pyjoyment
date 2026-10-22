#!/usr/bin/env python3
# A CGI program, which writes its response: the headers, an empty line and the body
import os
import urllib.parse


name = urllib.parse.parse_qs(os.environ.get('QUERY_STRING', '')).get('name', ['CGI'])[0]
print('Content-Type: text/plain; charset=UTF-8')
print()
print(f'Hello {name} at {os.environ["SCRIPT_NAME"]} for {os.environ["PATH_INFO"]}!')
