# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os import path
import unittest

from cloudify.test_utils import workflow_test

# This just gives us a path to the setup.py directory.
_plugin_directory = \
    '/{0}'.format(
        '/'.join(
            path.abspath(path.dirname(__file__)).split('/')[1:-2]
        )
    )
_blueprint_path = \
   path.join(_plugin_directory, 'examples/blueprint.yaml')


class TestPlugin(unittest.TestCase):

    @workflow_test(_blueprint_path)
    def test_workflow(self, cfy_local):
        # execute install workflow
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                )[0].runtime_properties.keys())
