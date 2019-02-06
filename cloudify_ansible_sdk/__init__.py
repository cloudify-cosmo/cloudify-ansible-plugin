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

from collections import namedtuple
from copy import deepcopy

from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.utils.display import Display

Options = namedtuple(
    'Options',
    [
        'ask_pass',
        'ask_su_pass',
        'ask_sudo_pass',
        'ask_vault_pass',
        'become',
        'become_ask_pass',
        'become_method',
        'become_user',
        'check',
        'connection',
        'diff',
        'extra_vars',
        'flush_cache',
        'force_handlers',
        'forks',
        'inventory',
        'listhosts',
        'listtags',
        'listtasks',
        'module_path',
        'private_key_file',
        'remote_user',
        'sftp_extra_args',
        'skip_tags',
        'syntax',
        'scp_extra_args',
        'ssh_common_args',
        'ssh_extra_args',
        'start_at_task',
        'step',
        'su',
        'subset',
        'sudo',
        'sudo_user',
        'su_user',
        'tags',
        'timeout',
        'vault_ids',
        'vault_password_files',
        'verbosity',
     ]
)


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

    # A lot of this stuff I did not have time to validate.
    def _set_options(self):
        _kwargs = deepcopy(self.options_config)
        if not isinstance(_kwargs, dict):
            raise CloudifyAnsibleSDKError(
                'options_config must be a dictionary.')
        if 'ask_pass' not in _kwargs:
            _kwargs['ask_pass'] = False
        if 'ask_su_pass' not in _kwargs:
            _kwargs['ask_su_pass'] = False
        if 'ask_sudo_pass' not in _kwargs:
            _kwargs['ask_sudo_pass'] = False
        if 'ask_vault_pass' not in _kwargs:
            _kwargs['ask_vault_pass'] = False
        if 'become' not in _kwargs:
            _kwargs['become'] = False
        if 'become_ask_pass' not in _kwargs:
            _kwargs['become_ask_pass'] = False
        if 'become_method' not in _kwargs:
            _kwargs['become_method'] = 'sudo'
        if 'become_user' not in _kwargs:
            _kwargs['become_user'] = 'root'
        if 'check' not in _kwargs:
            _kwargs['check'] = False
        if 'connection' not in _kwargs:
            _kwargs['connection'] = 'smart'
        if 'diff' not in _kwargs:
            _kwargs['diff'] = False
        if 'extra_vars' not in _kwargs:
            _kwargs['extra_vars'] = []
        if 'flush_cache' not in _kwargs:
            _kwargs['flush_cache'] = None
        if 'force_handlers' not in _kwargs:
            _kwargs['force_handlers'] = False
        if 'forks' not in _kwargs:
            _kwargs['forks'] = 10
        if 'inventory' not in _kwargs:
            _kwargs['inventory'] = self.inventory
        if 'listhosts' not in _kwargs:
            _kwargs['listhosts'] = None
        if 'listtags' not in _kwargs:
            _kwargs['listtags'] = None
        if 'listtasks' not in _kwargs:
            _kwargs['listtasks'] = None
        if 'module_path' not in _kwargs:
            _kwargs['module_path'] = self.modules
        if 'private_key_file' not in _kwargs:
            _kwargs['private_key_file'] = self.private_key_file
        if 'remote_user' not in _kwargs:
            _kwargs['remote_user'] = None
        if 'scp_extra_args' not in _kwargs:
            _kwargs['scp_extra_args'] = ''
        if 'sftp_extra_args' not in _kwargs:
            _kwargs['sftp_extra_args'] = ''
        if 'skip_tags' not in _kwargs:
            _kwargs['skip_tags'] = []
        if 'ssh_common_args' not in _kwargs:
            _kwargs['ssh_common_args'] = ''
        if 'ssh_extra_args' not in _kwargs:
            _kwargs['ssh_extra_args'] = ''
        if 'start_at_task' not in _kwargs:
            _kwargs['start_at_task'] = None
        if 'step' not in _kwargs:
            _kwargs['step'] = None
        if 'su' not in _kwargs:
            _kwargs['su'] = False
        if 'subset' not in _kwargs:
            _kwargs['subset'] = False
        if 'sudo' not in _kwargs:
            _kwargs['sudo'] = False
        if 'sudo_user' not in _kwargs:
            _kwargs['sudo_user'] = False
        if 'su_user' not in _kwargs:
            _kwargs['su_user'] = False
        if 'syntax' not in _kwargs:
            _kwargs['syntax'] = None
        if 'tags' not in _kwargs:
            _kwargs['tags'] = ['all']
        if 'timeout' not in _kwargs:
            _kwargs['timeout'] = 10
        if 'vault_ids' not in _kwargs:
            _kwargs['vault_ids'] = []
        if 'vault_password_files' not in _kwargs:
            _kwargs['vault_password_files'] = []
        if 'verbosity' not in _kwargs:
            _kwargs['verbosity'] = self.verbosity
        try:
            return Options(**_kwargs)
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

    def execute(self):
        # TODO: Catch this error: ansible.errors.AnsibleFileNotFound
        # TODO: Also: AnsibleParserError
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
