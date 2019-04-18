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
from os import environ, path
from unittest import skipUnless

from . import AnsibleTestBase

from ansible.executor.stats import AggregateStats
from .. import AnsiblePlaybookFromFile, CloudifyAnsibleSDKError


class AnsibleSDKTest(AnsibleTestBase):

    def test_that_tests_can_run_correctly(self):
        """Check that these tests can actually run."""
        self.assertTrue(path.isfile(self.playbook_path))
        self.assertTrue(path.isfile(self.hosts_path))
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
        """Check that we raise an error when an
        invalid inventory config is provided.
        """
        with self.assertRaises(CloudifyAnsibleSDKError):
            AnsiblePlaybookFromFile(
                self.playbook_path,
                self.hosts_path,
                ['host1', 'host2']
            )

    def test_variable_manager_raises(self):
        """Check that we raise an error when an
        invalid variable_manager config is provided.
        """
        with self.assertRaises(CloudifyAnsibleSDKError):
            AnsiblePlaybookFromFile(
                self.playbook_path,
                self.hosts_path,
                inventory_config=None,
                variable_manager_config=['host1', 'host2']
            )

    def test_options_raises(self):
        """Check that we raise an error when invalid options
        are provided.
        """
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
        """Check that our objects from Ansible
        that we are proxying are accessible.
        """
        pb = AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path
        )
        self.assertTrue(pb.tqm == pb.runner._tqm)
        self.assertTrue(pb.tqm_stats == pb.runner._tqm._stats)

    @patch('ansible.executor.playbook_executor.PlaybookExecutor.run')
    def test_execute(self, foo):
        """Check that run returns all the expected values."""
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
        """Check that with broken code run will raise an error."""
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
        """Check that our host success validation works."""

        x = deepcopy(self.mock_runner_return)
        mock_host = 'taco'
        foo.return_value = x

        pb = AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path)
        self.assertTrue(pb._host_success(mock_host))

        mock_dict = {mock_host: 1}
        x['failures'] = mock_dict
        foo.return_value = x

        pb = AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path)
        self.assertFalse(pb._host_success(mock_host))

    def test_validate_host_success(self):
        """Check that we can loop through our the playbook hosts."""
        mock_host = 'taco'
        mock_dict = {mock_host: 1}
        with patch('cloudify_ansible_sdk.AnsiblePlaybookFromFile.tqm_stats')\
                as foo:
            setattr(foo, 'processed', mock_dict)
            pb = AnsiblePlaybookFromFile(
                self.playbook_path,
                self.hosts_path)
            pb._validate_host_success()

    @patch('ansible.executor.task_queue_manager.TaskQueueManager.__init__')
    def test_task_queue_manager(self, foo):
        """Check that we initialize the TaskQueueManager
        when we initialize our Playbook object.
        """
        foo.return_value = None
        AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path)
        assert foo.called_once

    @patch('ansible.executor.playbook_executor.PlaybookExecutor.__init__')
    def test_playbook_executor(self, foo):
        """Check that we initialize the PlaybookExecutor
        when we initialize our Playbook object.
        """
        foo.return_value = None
        AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path)
        assert foo.called_once

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    def test_zplays(self):
        """Run an actual Ansible playbook from a file."""
        AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path).execute()
