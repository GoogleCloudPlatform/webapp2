# Copyright 2016 webapp2 AUTHORS All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# import os
# import sys
#
# from gcp.testing import appengine

#
# def pytest_configure():
#     appengine.pytest_configure()
#
#     # Prune the SDK's webapp2 path from sys.path to prevent loading the SDK's
#     # bundled webapp2.
#     import dev_appserver
#     gae_path = os.path.dirname(dev_appserver.__file__)
#     gae_webapp2_path = os.path.join(gae_path, 'lib', 'webapp2')
#
#     sys.path = [path for path in sys.path if gae_webapp2_path not in path]
