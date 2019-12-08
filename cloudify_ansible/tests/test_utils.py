# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import unittest
from mock import Mock
from tempfile import mkstemp

from cloudify.state import current_ctx
from cloudify.mocks import MockCloudifyContext
from cloudify.exceptions import NonRecoverableError

import cloudify_ansible.utils as utils


def download_resource_side_effect(*args, **kwargs):
    return args, kwargs


class UtilsTests(unittest.TestCase):

    def tearDown(self):
        current_ctx.clear()
        super(UtilsTests, self).tearDown()

    def _instance_ctx(self):
        _ctx = MockCloudifyContext(
            'node_name',
            properties={'d': 'c', 'b': 'a'},
            runtime_properties={'a': 'b', 'c': 'd'}
        )
        _ctx.download_resource = Mock(
            side_effect=download_resource_side_effect)
        current_ctx.set(_ctx)
        return _ctx

    def _relationship_ctx(self):
        _source = MockCloudifyContext(
            'source_name',
            properties={'s': 'o', 'r': 'c'},
            runtime_properties={'e': 'n', 'a': 'm'}
        )
        _target = MockCloudifyContext(
            'target_name',
            properties={'t': 'a', 'r': 'g'},
            runtime_properties={'e': 't', 'n': 'a'}
        )
        _ctx = MockCloudifyContext(
            source=_source,
            target=_target)
        current_ctx.set(_ctx)
        return _ctx

    def test_get_instance_instance(self):
        _ctx = self._instance_ctx()

        instance = utils._get_instance(_ctx)
        self.assertEqual(instance.runtime_properties,
                         {'a': 'b', 'c': 'd'})

    def test_get_instance_relationship(self):
        _ctx = self._relationship_ctx()

        instance = utils._get_instance(_ctx)
        self.assertEqual(instance.runtime_properties,
                         {'e': 'n', 'a': 'm'})

    def test_get_node_instance(self):
        _ctx = self._instance_ctx()

        node = utils._get_node(_ctx)
        self.assertEqual(node.properties,
                         {'d': 'c', 'b': 'a'})

    def test_get_node_relationship(self):
        _ctx = self._relationship_ctx()

        node = utils._get_node(_ctx)
        self.assertEqual(node.properties,
                         {'r': 'c', 's': 'o'})

    def test_get_source_config_from_ctx(self):
        _ctx = self._instance_ctx()
        _ctx.node.type_hierarchy = ['cloudify.nodes.Root']
        _ctx.instance.runtime_properties[utils.SOURCES] = {
            "all": {
                "hosts": {},
                "children": {}
            }
        }
        # check directly
        self.assertEqual(utils.get_source_config_from_ctx(_ctx),
                         {'all': {'children': {}, 'hosts': {}}})
        # check by remerge sources
        self.assertEqual(utils.get_remerged_config_sources(_ctx, {}),
                         {'all': {'children': {}, 'hosts': {}}})

    def test_get_remerged_config_sources(self):
        _ctx = self._relationship_ctx()
        _ctx.target.node.type_hierarchy = ['cloudify.nodes.Root']
        _ctx.source.node.type_hierarchy = ['cloudify.nodes.Root']
        _ctx.source.instance.runtime_properties[utils.SOURCES] = {
            "all": {
                "hosts": {},
                "children": {
                    'group_name': {
                        'hosts': {
                            'hostname_source': {
                                'ansible_become': True,
                                'ansible_ssh_common_args':
                                    '-o StrictHostKeyChecking=no'
                            }
                        }
                    }
                }
            }
        }

        self.assertEqual(
            utils.get_remerged_config_sources(_ctx, {
                'group_name': 'group_name',
                'hostname': 'hostname_target'
            }),
            {
                'all': {
                    'children': {
                        'group_name': {
                            'hosts': {
                                'hostname-target': {
                                    'ansible_become': True,
                                    'ansible_ssh_common_args':
                                        '-o StrictHostKeyChecking=no'
                                },
                                'hostname-source': {
                                    'ansible_become': True,
                                    'ansible_ssh_common_args':
                                        '-o StrictHostKeyChecking=no'
                                }
                            }
                        }
                    },
                    'hosts': {}}})

    def test_nested_file_path(self):
        ctx = self._instance_ctx()
        _, p = mkstemp()
        self.addCleanup(os.remove, p)
        output = utils.download_nested_file_to_new_nested_temp_file(
            p, p, ctx
        )
        self.assertEqual(output[0][1], p)

    def test_handle_file_path_no_string(self):
        class Foo(object):
            pass
        ctx = self._instance_ctx()
        self.assertRaises(
            NonRecoverableError,
            utils.handle_file_path,
            file_path=Foo,
            additional_playbook_files=[],
            _ctx=ctx,
        )

    def test_handle_file_path_additional_files(self):
        ctx = self._instance_ctx()
        _, p0 = mkstemp()
        _, p1 = mkstemp()
        _, p2 = mkstemp()
        _, p3 = mkstemp()
        addtl_files = [p1, p2, p3]
        output = utils.handle_file_path(p0, addtl_files, ctx)
        self.assertEqual(p0, output[0][0])
