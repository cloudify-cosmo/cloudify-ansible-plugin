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
from cStringIO import StringIO
import sys

from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.utils.display import Display

from cloudify_ansible_sdk.options import Options


class TossAnsibleOutput(list):
    """Ansible dumps a ton of junk to the screen which is not needed."""

    def __enter__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = self._stringio = StringIO()
        sys.stderr = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout
        sys.stderr = self._stderr


class CloudifyAnsibleSDKError(Exception):
    """Generic Error for handling issues preparing the Ansible Playbook."""
    pass


class AnsiblePlaybookFromFile(object):

    def __init__(self,
                 site_yaml_path,
                 sources='localhost,',
                 inventory_config=None,
                 variable_manager_config=None,
                 options_config=None,
                 passwords=None,
                 modules=None,
                 private_key_file=None,
                 run_data=None,
                 verbosity=2):

        self.display = Display(verbosity=verbosity)

        self.loader = DataLoader()
        self.modules = modules or []
        self.passwords = passwords or {'conn_pass': None, 'become_pass': None}
        self.private_key_file = private_key_file
        self.sources = sources
        self.site_yaml_path = site_yaml_path
        self.verbosity = verbosity

        # Configurations
        self.inventory_config = inventory_config or {}
        self.variable_manager_config = variable_manager_config or {}
        self.options_config = options_config or {}

        self.run_data = run_data or {}

        self.inventory = self._set_inventory()
        self.variable_manager = self._set_variable_manager()
        self.options = self._set_options()
        self.display.verbosity = self.options.verbosity

        self.tqm = self._set_task_manager()
        self.runner = self._set_runner()

    def _set_inventory(self):
        _kwargs = deepcopy(self.inventory_config)
        if not isinstance(_kwargs, dict):
            raise CloudifyAnsibleSDKError(
                'inventory_config must be a dictionary.')
        if 'loader' not in _kwargs:
            _kwargs.update({'loader': self.loader})
        if 'sources' not in _kwargs:
            _kwargs.update({'sources': self.sources})
        return InventoryManager(**_kwargs)

    def _set_variable_manager(self):
        _kwargs = deepcopy(self.variable_manager_config)
        if not isinstance(_kwargs, dict):
            raise CloudifyAnsibleSDKError(
                'variable_manager_config must be a dictionary.')
        if 'loader' not in _kwargs:
            _kwargs.update({'loader': self.loader})
        if 'inventory' not in _kwargs:
            _kwargs.update({'inventory': self.inventory})
        variable_manager = VariableManager(**_kwargs)
        variable_manager.extra_vars = self.run_data
        variable_manager.set_inventory(self.inventory)
        return variable_manager

    def _set_options(self):
        options_kwargs = deepcopy(self.options_config)
        if not isinstance(options_kwargs, dict):
            raise CloudifyAnsibleSDKError(
                'options_config must be a dictionary.')
        for k, v in self.options_defaults.items():
            if not options_kwargs.get(k):
                options_kwargs[k] = v
        try:
            return Options(**options_kwargs)
        except TypeError as e:
            raise CloudifyAnsibleSDKError(
                'Invalid options_config: {0}'.format(str(e)))

    def _set_task_manager(self):
        return TaskQueueManager(
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            options=self.options,
            passwords=self.passwords)

    def _set_runner(self):
        runner = PlaybookExecutor(
            playbooks=[self.site_yaml_path],
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            options=self.options,
            passwords=self.passwords)
        setattr(runner, '_tqm', self.tqm)
        return runner

    @property
    def tqm_stats(self):
        try:
            _stats = getattr(self.tqm, '_stats')
        except AttributeError as e:
            raise CloudifyAnsibleSDKError(
                'There is an issue with Ansible: {0}'.format(str(e))
            )
        return _stats

    @property
    def options_defaults(self):
        # A lot of this stuff I did not have time to validate.
        return {
            'ask_pass': False,
            'ask_su_pass': False,
            'ask_sudo_pass': False,
            'ask_vault_pass': False,
            'become': False,
            'become_ask_pass': False,
            'become_method': 'sudo',
            'become_user': 'root',
            'check': False,
            'connection': 'smart',
            'diff': False,
            'extra_vars': [],
            'flush_cache': None,
            'force_handlers': False,
            'forks': 10,
            'inventory': self.inventory,
            'listhosts': None,
            'listtags': None,
            'listtasks': None,
            'module_path': self.modules,
            'private_key_file': self.private_key_file,
            'remote_user': None,
            'scp_extra_args': '',
            'sftp_extra_args': '',
            'skip_tags': [],
            'ssh_common_args': '',
            'ssh_extra_args': '',
            'start_at_task': None,
            'step': None,
            'su': False,
            'su_user': False,
            'subset': False,
            'sudo': False,
            'sudo_user': False,
            'syntax': None,
            'tags': ['all'],
            'timeout': 10,
            'vault_ids': [],
            'vault_password_files': [],
            'verbosity': self.verbosity
        }

    def execute(self):
        # TODO: Catch this error: ansible.errors.AnsibleFileNotFound
        # TODO: Also: AnsibleParserError
        if self.verbosity < 2:
            with TossAnsibleOutput() as _:
                self.runner.run()
        else:
            self.runner.run()
        self.tqm.send_callback(
            'record_logs',
            user_id=self.run_data.get('user_id'),
            success=all(self.validate_host_success())
        )
        return self.tqm_stats

    def _host_success(self, host):
        host_summary = self.tqm_stats.summarize(host)
        dark_hosts = host_summary.get('unreachable') > 0
        failed_hosts = host_summary.get('failures') > 0
        if dark_hosts or failed_hosts:
            return False
        return True

    def validate_host_success(self):
        host_success = []
        for host in sorted(self.tqm_stats.processed.keys()):
            host_success.append(self._host_success(host))
        return host_success
