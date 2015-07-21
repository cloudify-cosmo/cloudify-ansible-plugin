########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import os
import testtools

from ansible_plugin import tasks
from cloudify.state import current_ctx
from cloudify.mocks import MockCloudifyContext


class TestAnsiblePluginUnitTests(testtools.TestCase):

    def get_mock_context(self, test_name):
        """ Creates a mock context """

        test_node_id = test_name

        test_properties = {
        }

        operation = {
            'retry_number': 0
        }

        ctx = MockCloudifyContext(
            node_id=test_node_id,
            properties=test_properties,
            operation=operation
        )

        return ctx

    def test_configure_operation(self):
        testname = __name__
        ctx = self.get_mock_context(testname)
        current_ctx.set(ctx=ctx)

        ctx.instance.runtime_properties['key'] = '~/.ssh/agent_key.pem'
        ctx.instance.runtime_properties['user'] = os.getlogin()
        tasks.configure(ctx=ctx)
        self.assertEqual(os.environ.get('ANSIBLE_CONFIG'),
                         os.path.expanduser('~/.ansible.cfg'))
        self.assertEqual(os.environ.get('USER'), os.getlogin())
        self.assertEqual(os.environ.get('HOME'), os.path.expanduser('~'))
        configuration = '[defaults]\n' \
                        'host_key_checking=False\n' \
                        'private_key_file={0}\n'.format(
                            os.path.expanduser(
                                ctx.instance.runtime_properties['key']))
        with open(os.environ.get('ANSIBLE_CONFIG'), 'r') as f:
            content = f.read()
        self.assertEqual(content, configuration)

    def test_configure_operation_no_user(self):
        testname = __name__
        ctx = self.get_mock_context(testname)
        current_ctx.set(ctx=ctx)

        ctx.instance.runtime_properties['key'] = '~/.ssh/agent_key.pem'
        ex = self.assertRaises(TypeError, tasks.configure, ctx=ctx)
        self.assertIn('must be string, not None', ex.message)

    def test_configure_operation_no_key(self):
        testname = __name__
        ctx = self.get_mock_context(testname)
        current_ctx.set(ctx=ctx)

        ctx.instance.runtime_properties['user'] = os.getlogin()
        ex = self.assertRaises(AttributeError, tasks.configure, ctx=ctx)
        self.assertIn("'NoneType' object has no attribute 'startswith'",
                      ex.message)

    def test_ansible_playbook_no_host(self):
        testname = __name__
        ctx = self.get_mock_context(testname)
        current_ctx.set(ctx=ctx)

        playbooks = []
        ex = self.assertRaises(AttributeError,
                               tasks.ansible_playbook,
                               playbooks, ctx=ctx)
        self.assertIn("object has no attribute 'host_ip'",
                      ex.message)
