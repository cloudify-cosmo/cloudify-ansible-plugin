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

import unittest
from mock import patch

from cloudify_ansible.tasks import _execute_playbook
from cloudify.exceptions import NonRecoverableError


@patch("cloudify_ansible_sdk.AnsiblePlaybookFromFile")
class AnsibleTasksTest(unittest.TestCase):

    def setUp(self):
        super(AnsibleTasksTest, self).setUp()

    def tearDown(self):
        super(AnsibleTasksTest, self).tearDown()

    def test_exception_raised(self, _):
        test_args = {
            'site_yaml_path': 'str',
            'sources': None,
            'inventory_config': ['host1', 'host2'],
        }
        with self.assertRaises(NonRecoverableError) as exc:
            _execute_playbook(test_args)
            self.assertIn('inventory_config must be a dictionary', exc)

    # @patch('ansible.executor.task_queue_manager.TaskQueueManager.__init__')
    # def test_task_queue_manager(self, foo):
    #     foo.return_value = None
    #     AnsiblePlaybookFromFile(
    #         self.playbook_path,
    #         self.hosts_path)
    #     assert foo.called_once
