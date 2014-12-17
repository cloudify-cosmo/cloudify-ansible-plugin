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

# ctx is imported and used in operations
from cloudify import ctx
# put the operation decorator on any function that is a task
from cloudify.decorators import operation
# Import Cloudify exception
from cloudify.exceptions import NonRecoverableError


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


def _install_package(package):
    """ Installs a Package
    """

    command = ['sudo', 'wget', 'https://bootstrap.pypa.io/get-pip.py']
    _run_shell_command(command)
    command = ['sudo', 'python', 'get-pip.py']
    _run_shell_command(command)
    ctx.logger.info('Begin installation: {0}'.format(package))
    command = ['sudo', 'pip', 'install', 'dev']
    _run_shell_command(command)
    command = ['sudo', 'pip', 'install', package]
    _run_shell_command(command)
    _validate_installation(package)


def _validate_installation(package):
    """ validate the installation
    """

    ctx.logger.info('Begin validation: {0}: '.format(package))
    command = [package, '--version']
    code = _run_shell_command(command)

    if code > 0:
        ctx.logger.info('Installation was unsuccessful')
    else:
        ctx.logger.info('Installation was successful')


@operation
def install(**kwargs):
    """ Wraps _install_package
    """

    if 'package_name' in kwargs.iteritems():
        package = package_name
    else:
        package = 'ansible'
    _install_package(package)
