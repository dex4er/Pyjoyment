#!/usr/bin/env python

# Usage:
#
#   python test.py
#   PROVE= python test.py
#   python setup.py
#   PYTHONPATH=`pwd` nosetests

import os
import subprocess
import sys
import unittest


dirs = ['t/Pyjo', 't/docs', 't/examples']


class TestSuite(unittest.TestSuite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        test_loader = unittest.defaultTestLoader
        for d in dirs:
            test_suite = test_loader.discover(d, pattern='*.py', top_level_dir='.')
            for t in test_suite:
                self.addTest(t)

    def __iter__(self):
        return iter(self._tests)


def run():
    try:
        if os.name == 'nt':
            default_prove = 'prove.bat'
        else:
            default_prove = 'prove'
        prove = os.getenv('PROVE', default_prove)
        args = sys.argv
        if len(args) > 2 and args[0].endswith('setup.py') and args[1] == 'test':
            args = args[2:]
        else:
            args = args[1:]
        if not list(map(lambda a: True if a.startswith('t/') else False, args)).count(True):
            args += dirs
        os.putenv('PYTHONPATH', '.')
        cmd = [prove, '--ext=py', '--exec=' + sys.executable] + args
        sys.exit(subprocess.call(cmd))
    except OSError:
        unittest.main(defaultTest='TestSuite')


if __name__ == '__main__':
    run()
