import Pyjo.App.FastCGI

from Pyjo.File import curfile
from Pyjoyment.Lite import *


# The scripts of PHP of the directory php under /php, on php-fpm with the pool of php/php-fpm.conf next to this script:
# php-fpm -n -y php/php-fpm.conf -F
fastcgi = Pyjo.App.FastCGI.new(url='fcgi://127.0.0.1:9000', document_root=curfile().sibling('php').to_str())
plugin('Mount', {'/php': fastcgi})

get('/', {'text': 'I ♥ Pyjoyment!'})

app.start()
