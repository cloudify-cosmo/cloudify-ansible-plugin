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
from cloudify_ansible_sdk import CloudifyAnsibleSDKError
from cloudify_ansible_sdk.sources import (
    AnsibleHost, AnsibleHostGroup, AnsibleSource, legalize_hostnames)


class TestHosts(AnsibleTestBase):

    def test_ansible_host(self):
        children = mock_sources_dict['all']['children']
        web_config = children['webservers']['hosts']['web']
        self.assertEquals(
            AnsibleHost('web', web_config).config,
            children['webservers']['hosts']['web']
        )
        db_config = children['dbservers']['hosts']['db']
        self.assertNotEquals(
            AnsibleHost('web', db_config).config,
            children['webservers']['hosts']['web']
        )

    def test_ansible_host_group(self):
        dbservers = AnsibleHostGroup('dbservers')
        children = mock_sources_dict['all']['children']
        db_host = children['dbservers']['hosts']['db']
        dbservers.insert_host('db', db_host)
        self.assertEquals(dbservers.name, 'dbservers')
        for key, value in dbservers.config['hosts']['db'].items():
            self.assertTrue(value == db_host[key])

    def test_ansible_source(self):
        ansible_source = AnsibleSource(mock_sources_dict)
        self.assertEqual(ansible_source.config, mock_sources_dict)
        new_group = {
            'all': {
                'hosts': {},
                'children': {
                    'lbs': {
                        'hosts': {
                            'lb': {
                                'ansible_host': 'foo',
                                'ansible_ssh_private_key_file': 'foo',
                                'ansible_user': 'foo',
                                'ansible_ssh_common_args':
                                    '-o StrictHostKeyChecking=no',
                            }
                        }
                    }
                }
            }
        }
        ansible_source.insert_children(
            'lbs', new_group['all']['children']['lbs'])
        old_mock_sources_dict = deepcopy(mock_sources_dict)
        old_mock_sources_dict['all']['children'].update(
            new_group['all']['children'])

        self.assertDictEqual(old_mock_sources_dict, ansible_source.config)
        mock_sources_dict['all']['children']['dbservers']['hosts'] = {
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
                      ansible_source.config
                      ['all']['children']['dbservers']['hosts'].keys())
        self.assertIn('db2',
                      ansible_source.config
                      ['all']['children']['dbservers']['hosts'].keys())

    def test_legalize_hostnames(self):
        self.assertEqual(legalize_hostnames("a-B_c-A"), "a-b-c-a")
        with self.assertRaisesRegexp(
            CloudifyAnsibleSDKError,
            'Hostname 1 is not a string'
        ):
            legalize_hostnames(1)

    def test_parse_sources(self):
        CHECK_FLAG = "-o StrictHostKeyChecking=no"
        INITIAL_STATE = {
            "hosts": {
                "kube-check": {
                    "parameters": {
                        "ansible_ssh_common_args": CHECK_FLAG
                    }
                }
            },
            "all": {
                "children": {
                    "k8s-cluster": {
                        "hosts": {
                            "kube-master-yynnoj": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            },
                            "kube-node-09q7do": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            }
                        }
                    }
                }
            }
        }
        FINAL_STATE = {
            "all": {
                "hosts": {
                    "kube-check": {
                        "ansible_ssh_common_args": CHECK_FLAG
                    }
                },
                "children": {
                    "k8s-cluster": {
                        "hosts": {
                            "kube-master-yynnoj": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            },
                            "kube-node-09q7do": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            }
                        }
                    }
                }
            }
        }
        ansible_source = AnsibleSource(INITIAL_STATE)
        self.assertEqual(ansible_source.config, FINAL_STATE)

    def test_merge_sources(self):
        CHECK_FLAG = "-o StrictHostKeyChecking=no"
        INITIAL_STATE = {
            "all": {
                "hosts": {},
                "children": {
                    "kube-master": {
                        "hosts": {
                            "kube-master-yynnoj": {
                                "ansible_ssh_common_args": CHECK_FLAG,
                                "ansible_become": True,
                                "ansible_ssh_private_key_file": "<some_key>",
                                "ansible_host": "10.239.1.177",
                                "ansible_user": "centos"
                            }
                        }
                    },
                    "k8s-cluster": {
                        "hosts": {
                            "kube-master-yynnoj": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            },
                            "kube-node-09q7do": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            }
                        }
                    },
                    "kube-node-group": {
                        "hosts": {
                            "kube-node-09q7do": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            }
                        }
                    },
                    "etcd": {
                        "hosts": {
                            "kube-master-yynnoj": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            }
                        }
                    },
                    "kube-master-group": {
                        "hosts": {
                            "kube-master-yynnoj": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            }
                        }
                    },
                    "kube-node": {
                        "hosts": {
                            "kube-node-09q7do": {
                                "ansible_ssh_common_args": CHECK_FLAG,
                                "ansible_become": True,
                                "ansible_ssh_private_key_file": "<some_key>",
                                "ansible_host": "10.239.1.176",
                                "ansible_user": "centos"
                            }
                        }
                    }
                }
            }
        }
        FINAL_STATE = {
            "all": {
                "hosts": {},
                "children": {
                    "kube-master": {
                        "hosts": {
                            "kube-master-yynnoj": {
                                "ansible_ssh_common_args": CHECK_FLAG,
                                "ansible_become": True,
                                "ansible_ssh_private_key_file": "<some_key>",
                                "ansible_host": "10.239.1.177",
                                "ansible_user": "centos"
                            }
                        }
                    },
                    "k8s-cluster": {
                        "hosts": {
                            "kube-node-sc3pxd": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            },
                            "kube-master-yynnoj": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            },
                            "kube-node-09q7do": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            }
                        }
                    },
                    "kube-node-group": {
                        "hosts": {
                            "kube-node-sc3pxd": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            },
                            "kube-node-09q7do": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            }
                        }
                    },
                    "etcd": {
                        "hosts": {
                            "kube-master-yynnoj": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            }
                        }
                    },
                    "kube-master-group": {
                        "hosts": {
                            "kube-master-yynnoj": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            }
                        }
                    },
                    "kube-node": {
                        "hosts": {
                            "kube-node-sc3pxd": {
                                "ansible_ssh_common_args": CHECK_FLAG,
                                "ansible_become": True,
                                "ansible_ssh_private_key_file": "<some_key>",
                                "ansible_host": "10.239.1.18",
                                "ansible_user": "centos"
                            },
                            "kube-node-09q7do": {
                                "ansible_ssh_common_args": CHECK_FLAG,
                                "ansible_become": True,
                                "ansible_ssh_private_key_file": "<some_key>",
                                "ansible_host": "10.239.1.176",
                                "ansible_user": "centos"
                            }
                        }
                    }
                }
            }
        }
        CHANGE_STATE = {
            "all": {
                "hosts": {},
                "children": {
                    "kube-node-group": {
                        "hosts": {
                            "kube-node-sc3pxd": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            }
                        }
                    },
                    "kube-node": {
                        "hosts": {
                            "kube-node-sc3pxd": {
                                "ansible_ssh_common_args": CHECK_FLAG,
                                "ansible_become": True,
                                "ansible_ssh_private_key_file": "<some_key>",
                                "ansible_host": "10.239.1.18",
                                "ansible_user": "centos"
                            }
                        }
                    },
                    "k8s-cluster": {
                        "hosts": {
                            "kube-node-sc3pxd": {
                                "ansible_ssh_common_args": CHECK_FLAG
                            }
                        }
                    }
                }
            }
        }
        # original sources
        ansible_source = AnsibleSource(INITIAL_STATE)
        # attach new one
        new_ansible_source = AnsibleSource(CHANGE_STATE)
        ansible_source.merge_source(new_ansible_source)
        self.maxDiff = None
        self.assertEqual(ansible_source.config, FINAL_STATE)
        # detach new one
        new_ansible_source = AnsibleSource(CHANGE_STATE)
        ansible_source.remove_source(new_ansible_source)
        self.assertEqual(ansible_source.config, INITIAL_STATE)
