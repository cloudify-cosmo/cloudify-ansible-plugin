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

HOSTS = 'hosts'
PLAYS = '___PLAYS'
IP = 'ansible_host'
SOURCES = 'sources'
USER = 'ansible_user'
WORKSPACE = 'workspace'
LOCAL_VENV = 'local_venv'
BECOME = 'ansible_become'
MODULE_PATH = 'module_path'
PLAYBOOK_VENV = 'playbook_venv'
SUPPORTED_PYTHON = ['3.6', '3.11']
INSTALLED_ROLES = 'installed_roles'
KEY = 'ansible_ssh_private_key_file'
COMPLETED_TAGS = '___COMPLETED_TAGS'
AVAILABLE_TAGS = '___AVAILABLE_STEPS'
ANSIBLE_TO_INSTALL = 'ansible==4.10.0'
SSH_COMMON = 'ansible_ssh_common_args'
COMPLETED_STEPS = '___COMPLETED_STEPS'
AVAILABLE_STEPS = '___AVAILABLE_STEPS'
NUMBER_OF_ATTEMPTS = 'number_of_attempts'
MODULE_NAME = 'cloudify_runtime_property.py'
OPTION_STDOUT_FORMAT = 'ANSIBLE_STDOUT_CALLBACK'
OPTION_HOST_CHECKING = 'ANSIBLE_HOST_KEY_CHECKING'
INSTALLED_PACKAGES = 'installed_ansible_venv_packages'
INSTALLED_COLLECTIONS = 'installed_galaxy_collections'
OPTION_TASK_FAILED_ATTRIBUTE = 'ANSIBLE_INVALID_TASK_ATTRIBUTE_FAILED'
BP_INCLUDES_PATH = '/opt/manager/resources/blueprints/' \
                   '{tenant}/{blueprint}/{relative_path}'
