# /// script
# requires-python = ">=3.12"
# dependencies = ["Pyjoyment"]
#
# [tool.uv.sources]
# Pyjoyment = { path = "../../.." }
# ///
from Pyjoyment.Lite import *

import platform
import ssl
import sys
import sysconfig


@get('/')
def index(c):
    c.render(text='Hello Pyjoyment on AWS Lambda, from a ZIP file!')


# The Python of the layer, of any version, also the free-threaded build, and the certificates of the system it reads
@get('/python')
def python(c):
    c.render(
        json={
            'version': platform.python_version(),
            'executable': sys.executable,
            'free_threaded': bool(sysconfig.get_config_var('Py_GIL_DISABLED')),
            'certificates': ssl.create_default_context().cert_store_stats()['x509_ca'],
        }
    )


# The handler "app.handler" of the event function, the runtime of the function when the bootstrap runs the script, and
# the command of the arguments otherwise
handler = app.start()
