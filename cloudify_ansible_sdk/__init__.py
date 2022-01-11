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

import os
import sys
import json
from tempfile import NamedTemporaryFile

from .constants import ansible_usage, ansible_playbook_usage

DEPRECATED_KEYS = [
    'site_yaml_path',
    'inventory_config',
    'variable_manager_config',
    'passwords',
    'modules',
    'private_key_file']
LIST_TYPES = ['skip-tags', 'tags']
DIRECT_PARAMS = ['start_at_task', 'scp_extra_args', 'sftp_extra_args',
                 'ssh_common_args', 'ssh_extra_args', 'timeout']


def get_fileno():
    try:
        return sys.stdout.fileno
    except AttributeError:
        return


class CloudifyAnsibleSDKError(Exception):
    """Generic Error for handling issues preparing
    the Ansible Playbook.
    """

    pass


class AnsiblePlaybookFromFile(object):
    """ Object for communication to Ansible Library."""

    def __init__(self,
                 playbook_path=None,
                 sources='localhost,',
                 options_config=None,
                 run_data=None,
                 verbosity=2,
                 logger=None,
                 site_yaml_path=None,
                 environment_variables=None,
                 additional_args=None,
                 start_at_task=None,
                 tags=None,
                 **kwargs):

        self.playbook = site_yaml_path or playbook_path
        self.sources = sources
        self._options_config = options_config or {}
        self.run_data = run_data or {}
        self.environment_variables = environment_variables or {}
        self.additional_args = additional_args or ''
        self._tags = tags
        self._verbosity = verbosity
        self.logger = logger

        for deprecated_key in DEPRECATED_KEYS:
            if deprecated_key in kwargs:
                self.logger.error(
                    'This key been deprecated: {0} {1}'.format(
                        deprecated_key, kwargs[deprecated_key]))

        # add known additional params to additional_args
        for field in DIRECT_PARAMS:
            if kwargs.get(field):
                self.additional_args += '--{field}="{value}" '.format(
                    field=field.replace("_", "-"),
                    value=json.dumps(kwargs[field]))
        if start_at_task:
            self.update_additional_args({'start_at_task': start_at_task})

    def update_additional_args(self, new_args):
        for key, value in new_args.items():
            self.additional_args += '--{field}="{value}" '.format(
                field=key.replace("_", "-"), value=value)

    @property
    def env(self):
        _env = os.environ.copy()
        for key, value in self.environment_variables.items():
            _env[key] = value
        return _env

    @property
    def verbosity(self):
        verbosity = '-v'
        for i in range(1, self._verbosity):
            verbosity += 'v'
        return verbosity

    @property
    def tags(self):
        if self._tags:
            if isinstance(self._tags, list):
                tags = ','.join(self._tags)
            else:
                tags = self._tags
            return '--tags "{tags}"'.format(tags=tags)
        return ''

    @property
    def options_config(self):
        return self._options_config

    @property
    def options(self):
        options_list = []
        if 'extra_vars' not in self.options_config:
            self.options_config['extra_vars'] = {}
        self.options_config['extra_vars'].update(self.run_data)
        for key, value in self.options_config.items():
            if key == 'extra_vars':
                f = NamedTemporaryFile(delete=False)
                with open(f.name, 'w') as outfile:
                    json.dump(value, outfile)
                value = '@{filepath}'.format(filepath=f.name)
            elif key == 'verbosity':
                self.logger.error('No such option verbosity')
                del key
                continue
            key = key.replace("_", "-")
            if isinstance(value, dict):
                value = json.dumps(value)
            elif isinstance(value, list) and key not in LIST_TYPES:
                value = [i for i in value]
            elif isinstance(value, list):
                value = u",".join(value)
            options_list.append(
                '--{key}={value}'.format(key=key, value=repr(value)))
        return ' '.join(options_list)

    @property
    def process_args(self):
        for key in list(self.options_config.keys()):
            key_usage = key.replace('_', '-')
            if key_usage not in ansible_playbook_usage:
                self.logger.debug(
                    'Removing invalid flag from options_config: '
                    '{flag}.'.format(flag=key))
                del self._options_config[key]
        return [
            self.verbosity,
            '-i {0}'.format(self.sources),
            self.options,
            self.playbook,
            self.additional_args,
            self.tags,
        ]

    @property
    def facts_args(self):
        for key in list(self.options_config.keys()):
            key_usage = key.replace('_', '-')
            if key_usage not in ansible_usage:
                self.logger.debug(
                    'Removing invalid flag from options_config: '
                    '{flag}.'.format(flag=key))
                del self._options_config[key]
        return [
            self.verbosity,
            '-i {0}'.format(self.sources),
            self.options,
            '-m setup all'
        ]

    @staticmethod
    def execute(process_execution_func, **kwargs):
        return process_execution_func(**kwargs)

    @staticmethod
    def get_facts(process_execution_func, **kwargs):
        return process_execution_func(**kwargs)
