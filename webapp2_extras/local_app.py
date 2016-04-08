# -*- coding: utf-8 -*-
# Copyright 2011 webapp2 AUTHORS.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
webapp2_extras.local_app
~~~~~~~~~~~~~~~~~~~~~~~~

This module is deprecated. The functionality is now available
directly in webapp2.

Previously it implemented a WSGIApplication adapted for threaded
environments.
"""
import warnings

import webapp2

warnings.warn(DeprecationWarning(
    'webapp2_extras.local_app is deprecated. webapp2.WSGIApplication is now '
    'thread-safe by default when webapp2_extras.local is available.'),
    stacklevel=1)

WSGIApplication = webapp2.WSGIApplication
