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

from logging import getLogger
from mock import patch, Mock
from os import environ, path
from unittest import skipUnless

from . import AnsibleTestBase

from .. import AnsiblePlaybookFromFile


class AnsibleSDKTest(AnsibleTestBase):

    def test_that_tests_can_run_correctly(self):
        """Check that these tests can actually run."""
        self.assertTrue(path.isfile(self.playbook_path))
        self.assertTrue(path.isfile(self.hosts_path))
        self.assertIn(
            self.hosts_path,
            AnsiblePlaybookFromFile(
                self.playbook_path,
                self.hosts_path, logger=getLogger('testLogger')).sources)
        self.assertIn(
            self.playbook_path,
            AnsiblePlaybookFromFile(
                self.playbook_path,
                self.hosts_path, logger=getLogger('testLogger')).playbook)

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    def test_zplays(self):
        """Run an actual Ansible playbook from a file."""
        AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path,
            logger=getLogger('testLogger')
        ).execute()

    def test_env(self):
        test_env = environ.copy()
        new = {'foo': 'bar'}
        p = AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path,
            environment_variables=new,
            logger=getLogger('testLogger')
        )
        test_env.update(new)
        self.assertEqual(p.env, test_env)

    def test_verbosity(self):
        p = AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path,
            verbosity=5,
            logger=getLogger('testLogger')
        )
        self.assertEqual(p.verbosity, '-vvvvv')

    def test_options(self):
        p = AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path,
            run_data={'taco': 'foo'},
            options_config={'foo': 'bar'},
            logger=getLogger('testLogger')
        )
        self.assertIn('--foo=bar', p.options)
        if 'extra-vars' in p.options:
            self.assertIn('@', p.options)

    def test_command(self):
        p = AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path,
            logger=getLogger('testLogger')
        )
        self.assertEqual(p.command.split(' ')[0],
                         'ansible-playbook')
        self.assertEqual(p.command.split(' ')[1],
                         '-vv')
        self.assertEqual(p.command.split(' ')[2],
                         '-i')
        self.assertIn('ansible-examples/lamp_simple/hosts',
                      p.command.split(' ')[3])
        self.assertIn('ansible-examples/lamp_simple/site.yml',
                      p.command.split(' ')[5])

    def test_execute(self):
        p = AnsiblePlaybookFromFile(
            self.playbook_path,
            self.hosts_path,
            logger=getLogger('testLogger')
        )
        with patch('subprocess.Popen') as mopen:
            process_mock = Mock()
            attrs = {'wait.return_value': 0, 'stdout': []}
            process_mock.configure_mock(**attrs)
            p.execute()
            self.assertTrue(mopen.called)
