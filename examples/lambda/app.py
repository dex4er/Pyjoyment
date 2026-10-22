import Pyjo.App.FastCGI

from Pyjoyment.Lite import *

import os
import subprocess
import time


@get('/')
def index(c):
    c.render(text='Hello Pyjoyment on AWS Lambda!')


# What the function gets of a request, after the load balancer and the event
@any('/echo')
def echo(c):
    req = c.req
    c.render(
        json={
            'method': req.method,
            'path': req.url.path.to_str(),
            'query': req.query_params.to_dict(),
            'body': req.text,
        }
    )


# PHP of a layer with php-fpm, as the one of Bref in the variable "layers", started with the execution environment, with
# phpinfo.php under /php
if os.path.exists('/opt/bin/php-fpm'):
    with open('/tmp/php-fpm.conf', 'w') as f:
        f.write(
            '[global]\nerror_log = /proc/self/fd/2\ndaemonize = no\n'
            '[www]\nlisten = /tmp/php-fpm.sock\npm = static\npm.max_children = 1\n'
            'clear_env = no\ncatch_workers_output = yes\n'
        )
    php_fpm = subprocess.Popen(['/opt/bin/php-fpm', '-n', '-y', '/tmp/php-fpm.conf', '-F'])
    for _ in range(50):
        if os.path.exists('/tmp/php-fpm.sock'):
            break
        time.sleep(0.1)
    fastcgi = Pyjo.App.FastCGI.new(url='fcgi+unix://%2Ftmp%2Fphp-fpm.sock', script='/var/task/phpinfo.php')
    plugin('Mount', {'/php': fastcgi})


# The handler "app.handler" of the event function, and the command of the arguments otherwise
handler = app.start()
