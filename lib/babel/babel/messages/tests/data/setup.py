#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: setup.py 114 2007-06-14 21:17:14Z palgarvio $
# =============================================================================
# $URL: http://svn.edgewall.org/repos/babel/trunk/babel/messages/tests/data/setup.py $
# $LastChangedDate: 2007-06-14 18:17:14 -0300 (Thu, 14 Jun 2007) $
# $Rev: 114 $
# $LastChangedBy: palgarvio $
# =============================================================================
# Copyright (C) 2006 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

# THIS IS A BOGUS PROJECT

from setuptools import setup, find_packages

setup(
    name = 'TestProject',
    version = '0.1',
    license = 'BSD',
    author = 'Foo Bar',
    author_email = 'foo@bar.tld',
    packages = find_packages(),
)
