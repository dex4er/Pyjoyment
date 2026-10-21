import Pyjo.App.FastCGI

from Pyjo.File import curfile
from Pyjoyment.Lite import *


# PHP on php-fpm under /php, with the pool of php/php-fpm.conf next to this script: php-fpm -n -y php/php-fpm.conf -F
php = curfile().sibling('php')
fastcgi = Pyjo.App.FastCGI.new(
    url='fcgi://127.0.0.1:9000',
    env={'SCRIPT_FILENAME': php.child('index.php').to_str(), 'DOCUMENT_ROOT': php.to_str()},
)
plugin('Mount', {'/php': fastcgi})

get('/', {'text': 'I ♥ Pyjoyment!'})

app.start()
