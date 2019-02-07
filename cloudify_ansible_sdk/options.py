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
