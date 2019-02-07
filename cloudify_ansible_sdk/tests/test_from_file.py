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

from copy import deepcopy
from mock import patch
import os
import unittest

from ansible.executor.stats import AggregateStats
from .. import AnsiblePlaybookFromFile, CloudifyAnsibleSDKError


class AnsibleSDKHandlerTest(unittest.TestCase):

    _CWD = os.path.abspath(os.path.dirname(__file__))

    def setUp(self):
        super(AnsibleSDKHandlerTest, self).setUp()

    def tearDown(self):
        super(AnsibleSDKHandlerTest, self).tearDown()

    @property
    def cwd(self):
        path_components = self._CWD.split('/')[1:-2]
        _cwd = '/'.join(path_components)
        _cwd = '/{0}'.format(_cwd)
        return _cwd

    @property
    def playbook_path(self):
        return os.path.join(
            self.cwd,
            'examples/ansible-examples/lamp_simple/site.yml'
        )

    @property
    def hosts_path(self):
        return os.path.join(
            self.cwd,
            'examples/ansible-examples/lamp_simple/hosts'
        )

    @property
    def mock_runner_return(self):
        return {
            'skipped': {},
            'ok': {},
            'changed': {},
            'custom': {},
            'dark': {},
            'processed': {},
            'failures': {}
        }

    def test_required_files(self):
        self.assertTrue(os.path.isfile(self.playbook_path))
        self.assertTrue(os.path.isfile(self.hosts_path))

    def test_loads_files(self):
        self.assertIn(
            self.hosts_path,
            AnsiblePlaybookFromFile(
                self.playbook_path,
                self.hosts_path).inventory._sources)
        self.assertIn(
            self.playbook_path,
            AnsiblePlaybookFromFile(
                self.playbook_path,
                self.hosts_path).runner._playbooks)

    def test_inventory_raises(self):
        with self.assertRaises(CloudifyAnsibleSDKError):
            AnsiblePlaybookFromFile(
                self.playbook_path,
                self.hosts_path,
                ['host1', 'host2']
            )

    def test_variable_manager_raises(self):
        with self.assertRaises(CloudifyAnsibleSDKError):
            AnsiblePlaybookFromFile(
                self.playbook_path,
                self.hosts_path,
                inventory_config=None,
                variable_manager_config=['host1', 'host2']
            )

    def test_options_raises(self):
        with self.assertRaises(CloudifyAnsibleSDKError):
            AnsiblePlaybookFromFile(
                self.playbook_path,
                self.hosts_path,
                inventory_config=None,
                variable_manager_config=None,
                options_config='foo'
            )
        with self.assertRaises(CloudifyAnsibleSDKError):
            AnsiblePlaybookFromFile(
                self.playbook_path,
                self.hosts_path,
                inventory_config=None,
                variable_manager_config=None,
                options_config={'foo': 'bar'}
            )

    def test_proxies(self):
        pb = AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path
        )
        self.assertTrue(pb.tqm == pb.runner._tqm)
        self.assertTrue(pb.tqm_stats == pb.runner._tqm._stats)

    @patch('ansible.executor.playbook_executor.PlaybookExecutor.run')
    def test_execute(self, foo):
        instance = foo.return_value
        instance.method.return_value = self.mock_runner_return
        pb = AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path)
        pb.execute()
        self.assertTrue(
            isinstance(pb.tqm_stats, AggregateStats))
        self.assertEqual(
            pb.tqm_stats.__dict__,
            self.mock_runner_return)

    @patch('ansible.executor.playbook_executor.PlaybookExecutor.run')
    def test_tqm_stats(self, foo):
        instance = foo.return_value
        instance.method.return_value = self.mock_runner_return
        with self.assertRaises(CloudifyAnsibleSDKError):
            pb = AnsiblePlaybookFromFile(
                self.playbook_path,
                self.hosts_path
            )
            del pb.tqm._stats
            pb.execute()

    @patch('ansible.executor.stats.AggregateStats.summarize')
    def test_host_success(self, foo):

        x = deepcopy(self.mock_runner_return)
        mock_host = 'taco'
        mock_dict = {mock_host: 1}

        pb = AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path)
        self.assertTrue(pb._host_success(mock_host))

        x['failures'] = mock_dict
        foo.return_value = x

        pb = AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path)
        self.assertFalse(pb._host_success(mock_host))

    def test_validate_host_success(self):
        mock_host = 'taco'
        mock_dict = {mock_host: 1}
        with patch('cloudify_ansible_sdk.AnsiblePlaybookFromFile.tqm_stats')\
                as foo:
            setattr(foo, 'processed', mock_dict)
            pb = AnsiblePlaybookFromFile(
                self.playbook_path,
                self.hosts_path)
            pb.validate_host_success()

    @patch('ansible.executor.task_queue_manager.TaskQueueManager.__init__')
    def test_task_queue_manager(self, foo):
        foo.return_value = None
        AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path)
        assert foo.called_once

    @patch('ansible.executor.playbook_executor.PlaybookExecutor.__init__')
    def test_playbook_executor(self, foo):
        foo.return_value = None
        AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path)
        assert foo.called_once

    @unittest.skipUnless(
        os.environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    def test_zplays(self):
        AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path).execute()
