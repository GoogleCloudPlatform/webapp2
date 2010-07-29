# -*- coding: utf-8 -*-
"""
To run the tests, first install the following packages:

    nose
    nosegae==0.1.7
    webtest
    gaetestbed
    coverage

Then run run_tests.py.
"""
import os
import sys

import nose

if __name__ == '__main__':
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, base)

    argv = [__file__]
    argv += '-d --with-gae -P --without-sandbox --cover-erase --with-coverage --cover-package=webapp2 --gae-application=../example'.split()
    nose.run(argv=argv)
