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


class AnsibleSource(object):

    def __init__(self, source_dict):

        source_dict = source_dict or {}
        self.groups = {}

        for group_name, group_config in source_dict.items():
            self.insert_group(group_name, group_config)

    def insert_group(self, name, config=None):
        config = config or {}
        self.groups[name] = AnsibleHostGroup(name, **config)

    def merge_source(self, ansible_source):
        for group_name, group in ansible_source.groups.items():
            if group_name in self.groups:
                local_group = self.groups.get(group_name)
                for hostname, host in local_group.hosts.items():
                    group.insert_host(hostname, host.config)
            self.insert_group(group_name, group.config)

    @property
    def config(self):
        new_dict = {}
        for group_name, group in self.groups.items():
            new_dict[group_name] = group.config
        return new_dict


class AnsibleHostGroup(object):

    def __init__(self, name, hosts=None):

        self.name = name
        self.hosts = {}

        hosts = hosts or {}

        for hostname, host_config in hosts.items():
            self.insert_host(hostname, host_config)

    def insert_host(self, hostname, config):
        self.hosts[hostname] = AnsibleHost(hostname, config)

    @property
    def config(self):
        new_dict = {}
        for hostname, host in self.hosts.items():
            new_dict.update({hostname: host.config})
        return {'hosts': new_dict}


class AnsibleHost(object):

    def __init__(self, hostname, parameters):

        parameters = parameters or {}

        self.name = hostname

        self.ansible_host = parameters['ansible_host']
        self.ansible_user = parameters['ansible_user']
        self.ansible_ssh_private_key_file = parameters.get(
            'ansible_ssh_private_key_file')

        self.ansible_become = parameters.get('ansible_become')
        self.ansible_ssh_common_args = parameters.get(
            'ansible_ssh_common_args')

        self.config = {
            'ansible_host': self.ansible_host,
            'ansible_user': self.ansible_user,
            'ansible_ssh_private_key_file':
                self.ansible_ssh_private_key_file,
        }

        if self.ansible_become:
            self.config['ansible_become'] = self.ansible_become

        if self.ansible_ssh_common_args:
            self.config['ansible_ssh_common_args'] = \
                self.ansible_ssh_common_args
