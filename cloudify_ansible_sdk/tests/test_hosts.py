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

from . import mock_sources_dict, AnsibleTestBase
from cloudify_ansible_sdk.sources import (
    AnsibleHost, AnsibleHostGroup, AnsibleSource)

import pprint
pp = pprint.PrettyPrinter(indent=4)


class TestHosts(AnsibleTestBase):

    def test_ansible_host(self):
        web_config = mock_sources_dict['webservers']['hosts']['web']
        self.assertEquals(
            AnsibleHost('web', web_config).config,
            mock_sources_dict['webservers']['hosts']['web']
        )
        db_config = mock_sources_dict['dbservers']['hosts']['db']
        self.assertNotEquals(
            AnsibleHost('web', db_config).config,
            mock_sources_dict['webservers']['hosts']['web']
        )

    def test_ansible_host_group(self):
        dbservers = AnsibleHostGroup('dbservers')
        db_host = mock_sources_dict['dbservers']['hosts']['db']
        dbservers.insert_host('db', db_host)
        self.assertEquals(dbservers.name, 'dbservers')
        for key, value in dbservers.config['hosts']['db'].items():
            self.assertTrue(value == db_host[key])

    def test_ansible_source(self):
        ansible_source = AnsibleSource(mock_sources_dict)
        self.assertEqual(ansible_source.config, mock_sources_dict)
        new_group = {
            'lbs': {
                'hosts': {
                    'lb': {
                        'ansible_host': 'foo',
                        'ansible_ssh_private_key_file': 'foo',
                        'ansible_user': 'foo',
                    }
                }
            }
        }
        ansible_source.insert_group('lbs', new_group['lbs'])
        old_mock_sources_dict = deepcopy(mock_sources_dict)
        old_mock_sources_dict.update(new_group)
        self.assertEqual(old_mock_sources_dict, ansible_source.config)
        mock_sources_dict['dbservers']['hosts'] = {
            'db1': {
                'ansible_host': 'bar',
                'ansible_ssh_private_key_file': 'bar',
                'ansible_user': 'bar',
            },
            'db2': {
                'ansible_host': 'taco',
                'ansible_ssh_private_key_file': 'taco',
                'ansible_user': 'taco',
            }
        }
        new_ansible_source = AnsibleSource(mock_sources_dict)
        ansible_source.merge_source(new_ansible_source)
        self.assertIn('db1',
                      ansible_source.config['dbservers']['hosts'].keys())
        self.assertIn('db2',
                      ansible_source.config['dbservers']['hosts'].keys())
