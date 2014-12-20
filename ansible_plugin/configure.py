########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License,  Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#                http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,  software
# distributed under the License is distributed on an 'AS IS' BASIS,
#   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,  either express or implied.
#   * See the License for the specific language governing permissions and
#   * limitations under the License.

# for running shell commands
import subprocess
import os
import errno

# ctx is imported and used in operations
from cloudify import ctx
# put the operation decorator on any function that is a task
from cloudify.decorators import operation
# Import Cloudify exception
from cloudify.exceptions import NonRecoverableError


@operation
def configure(**kwargs):

    deployment_directory = '/home/ubuntu/cloudify.' + ctx.deployment.id
    ansible_binary = deployment_directory + '/env/bin/ansible'

    if _validate(ansible_binary):
        ctx.logger.info('Confirmed that ansible is on the manager.')
    else:
        ctx.logger.error('Unable to confirm that ansible is on the manager.')
        exit(1)

    if 'ansible_home' in kwargs:
        ansible_home = kwargs['ansible_home']
    else:
        ansible_home = deployment_directory + '/etc/ansible'

    paths = [ansible_home,
             ansible_home + '/group_vars',
             ansible_home + '/host_vars',
             ansible_home + '/library',
             ansible_home + '/filter_plugins',
             ansible_home + '/roles',
             ansible_home + '/roles/common',
             ansible_home + '/roles/common/tasks',
             ansible_home + '/roles/common/handlers',
             ansible_home + '/roles/common/templates',
             ansible_home + '/roles/common/files',
             ansible_home + '/roles/common/vars',
             ansible_home + '/roles/common/defaults',
             ansible_home + '/roles/common/meta',
             ansible_home + '/webtier',
             ansible_home + '/monitoring']

    for path in paths:
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    command = ['echo', '"[defaults]\nhost_key_checking = False"', ">>",
               '/home/ubuntu/.ansible.cfg']
    _run_shell_command(command)


def _validate(ansible_binary):
    """ validate that ansible is installed on the manager
    """

    ctx.logger.info('Validating that {0} is installed on the manager.'
                    .format('ansible'))

    command = [ansible_binary, '--version']
    code = _run_shell_command(command)

    if code > 0:
        ctx.logger.info('Installation was unsuccessful')
        return False
    else:
        ctx.logger.info('Installation was successful')
        return True


def _run_shell_command(command):
    """Runs a shell command
    """

    ctx.logger.info('Running shell command: {0}'.format(command))
    try:
        run = subprocess.check_call(
            command)
    except subprocess.CalledProcessError:
        ctx.logger.error('Unable to run shell command: {0}'.format(command))
        raise NonRecoverableError('Command failed: {0}'.format(command))
    return run
