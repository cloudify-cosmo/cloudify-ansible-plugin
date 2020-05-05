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

from cloudify_ansible_sdk import CloudifyAnsibleSDKError
from cloudify_ansible_sdk._compat import text_type


def legalize_hostnames(hostname):
    if not isinstance(hostname, (text_type, bytes)):
        raise CloudifyAnsibleSDKError(
            'Hostname {0} is not a string'.format(hostname))
    hostname = u'{0}'.format(hostname.replace('_', '-'))
    return hostname.lower()


class AnsibleSource(object):

    def __init__(self, source_dict):

        source_dict = source_dict or {}
        self.children = {}
        self.hosts = {}

        if 'all' in source_dict:
            self.do_insert_children(source_dict['all'].get('children', {}))
            self.do_insert_hosts(source_dict.get('hosts', {}))
        else:
            for name, config in source_dict.items():
                self.insert_children(name, config)

    def do_insert_children(self, group_dict):
        for name, config in group_dict.items():
            self.insert_children(name, config)

    def do_insert_hosts(self, hosts_dict):
        for name, config in hosts_dict.items():
            self.insert_hosts(name, config)

    def insert_children(self, name, config=None):
        config = config or {}
        self.children[name] = AnsibleHostGroup(name, **config)

    def insert_hosts(self, name, config=None):
        name = legalize_hostnames(name)
        config = config or {}
        self.hosts[name] = AnsibleHost(name, **config)

    def merge_source(self, ansible_source):
        for group_name, group in ansible_source.children.items():
            if group_name in self.children:
                local_group = self.children.get(group_name)
                for hostname, host in local_group.hosts.items():
                    group.insert_host(hostname, host.config)
            self.insert_children(group_name, group.config)

    def remove_source(self, ansible_source):
        for group_name, group in ansible_source.children.items():
            if group_name in self.children:
                local_group = self.children.get(group_name)
                for hostname, _ in group.hosts.items():
                    local_group.remove_host(hostname)

    @property
    def config(self):
        new_dict = {
            'all': {
                'hosts': {},
                'children': {},
            },
        }
        for group_name, group in self.children.items():
            new_dict['all']['children'].update({group_name: group.config})
        for hostname, host in self.hosts.items():
            hostname = legalize_hostnames(hostname)
            new_dict['all']['hosts'].update({hostname: host.config})
        return new_dict


class AnsibleHostGroup(object):

    def __init__(self, name, hosts=None):

        self.name = name
        self.hosts = {}

        hosts = hosts or {}

        for hostname, host_config in hosts.items():
            self.insert_host(hostname, host_config)

    def insert_host(self, hostname, config):
        hostname = legalize_hostnames(hostname)
        self.hosts[hostname] = AnsibleHost(hostname, config)

    def remove_host(self, hostname):
        hostname = legalize_hostnames(hostname)
        if hostname in self.hosts:
            del self.hosts[hostname]

    @property
    def config(self):
        new_dict = {}
        for hostname, host in self.hosts.items():
            hostname = legalize_hostnames(hostname)
            new_dict.update({hostname: host.config})
        return {'hosts': new_dict}


class AnsibleHost(object):

    def __init__(self, hostname, parameters):

        parameters = parameters or {}

        self.name = legalize_hostnames(hostname)

        self.ansible_host = parameters.get('ansible_host')
        self.ansible_user = parameters.get('ansible_user')
        self.ansible_ssh_pass = parameters.get('ansible_ssh_pass')
        self.ansible_ssh_private_key_file = parameters.get(
            'ansible_ssh_private_key_file')

        self.ansible_become = parameters.get('ansible_become')
        self.ansible_ssh_common_args = parameters.get(
            'ansible_ssh_common_args', '-o StrictHostKeyChecking=no')

        self.config = {}
        if self.ansible_host:
            self.config['ansible_host'] = self.ansible_host
        if self.ansible_user:
            self.config['ansible_user'] = self.ansible_user
        if self.ansible_ssh_pass:
            self.config['ansible_ssh_pass'] = self.ansible_ssh_pass
        if self.ansible_ssh_private_key_file:
            self.config['ansible_ssh_private_key_file'] = \
                self.ansible_ssh_private_key_file
        if self.ansible_become:
            self.config['ansible_become'] = self.ansible_become
        if self.ansible_ssh_common_args:
            self.config['ansible_ssh_common_args'] = \
                self.ansible_ssh_common_args
