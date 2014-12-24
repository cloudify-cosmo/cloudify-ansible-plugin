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
import os
from os.path import join as joinpath
import errno

# ctx is imported and used in operations
from cloudify import ctx
# put the operation decorator on any function that is a task
from cloudify.decorators import operation
# Import Cloudify exception
from cloudify.exceptions import NonRecoverableError


DEFAULT_ANSIBLE_BEST_PRACTICES_DIRECTORY_TREE = [
    'group_vars',
    'host_vars',
    'library',
    'filter_plugins',
    'roles',
    'roles/common',
    'roles/common/tasks',
    'roles/common/handlers',
    'roles/common/templates',
    'roles/common/files',
    'roles/common/vars',
    'roles/common/defaults',
    'roles/common/meta',
    'webtier',
    'monitoring'
]

@operation
def make_directories(user_home = '/home/ubuntu', ansible_conf = 'ansible.cfg', **kwargs):

    deployment_home = joinpath(user_home, 'cloudify.', ctx.deployment.id)
    etc_ansible = joinpath(deployment_home, 'env', 'etc', 'ansible')

    create_directories(etc_ansible, DEFAULT_ANSIBLE_BEST_PRACTICES_DIRECTORY_TREE)


@operation
def put_ansible_conf(user_home = '/home/ubuntu', ansible_conf = 'ansible.cfg', **kwargs):

    if download_resource(ansible_conf, joinpath(user_home, '.ansible.cfg') ):
        ctx.logger.info("Ansible configured.")
    else:
        ctx.logger.info('Ansible not configured.')
        raise NonRecoverableError('Ansible not configured.')

@operation
def validate(user_home = '/home/ubuntu', binary_name = 'ansible-playbook', **kwargs):
    """ validate that ansible is installed on the manager
    """

    deployment_home = joinpath(user_home, 'cloudify.', ctx.deployment.id)
    playbook_binary = joinpath(deployment_home, 'env', 'bin', binary_name)

    command = [playbook_binary, '--version']
    code = run_shell_command(command)

    if code == 0:
        ctx.logger.info('Confirmed that ansible is installed on the manager.')
    else:
        ctx.logger.error('Unable to verify ansible installation.')

@operation
def hard_code_home(user_home = '/home/ubuntu', **kwargs):
    """ Ansible configures a writable directory in '$HOME/.ansible/cp',mode=0700
    Cloudify's workers can't use that variable, so we need to hard code the home.
    """

    deployment_home = joinpath(user_home, 'cloudify.', ctx.deployment.id)

    user_home = user_home[1:]
    home, user = user_home.split('/')

    ansible_files = [deployment_home + '/env/lib/python2.7/site-packages/ansible/runner/connection_plugins/ssh.py',
                     deployment_home + '/env/local/lib/python2.7/site-packages/ansible/runner/connection_plugins/ssh.py']

    for ansible_file in ansible_files:
        replace_string(ansible_file, '$HOME', joinpath('/', home, user))

def download_resource(file, target_file):
    """ copies 'file' from local machine and moves to
    target_file
    """

    try:
        ctx.download_resource(file, target_file)
    except Error as e:
        print('Error {0}'.format(e))
        raise exceptions.NonRecoverableError(
            'Could not get "{0}" ({1}: {2})'.format(
                file, type(e).__name__, e))
        return False

    return True

def create_directories(etc_ansible, paths):

    for path in paths:
        makeme = joinpath(etc_ansible, path)
        try:
            os.makedirs(makeme)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise NonRecoverableError('Cannot create directory {0}, error: {1}'.format(path, e))

def replace_string(file, old_string, new_string):

    new_file = joinpath('/tmp', file)

    with open(new_file, 'wt') as fout:
        with open(file, 'rt') as fin:
            for line in fin:
                fout.write(line.replace(old_string, new_search))

    copy(new_file, file)
    os.remove(new_file)

def write_to_file(path, filename, entry):

    if not pathexists(path):
        makedirs(path)

    path_to_file = joinpath(path, filename)

    if not pathexists(path_to_file):
        try:
            f = open(path_to_file, 'w')
            f.write(entry)
            success = True
        except IOError as e:
            ctx.logger.error('Can\'t open file {0} for writing: {1}'.format(path_to_file, e))
            success = False
    else:
        try:
            f = open(path_to_file, 'a')
            f.write(entry)
            success = True
        except IOError as e:
            ctx.logger.error('Can\'t open file {0} for writing: {1}'.format(path_to_file, e))
            success = False
        f.close()

    return success


def run_shell_command(command):
    """this runs a shell command.
    """
    ctx.logger.info("Running shell command: {0}"
                    .format(command))

    try:
        run = subprocess.Popen(command, stdout=subprocess.PIPE)
        output, error = run.communicate()
        if output:
            ctx.logger.info('lines: {0}'.format(output))
        elif error:
            ctx.logger.error('error: {0}'.format(error))
            raise Exception('{0} returned {1}'.format(command, error))
    except:
        ctx.logger.error('Unknown Exception, command: {0}'.format(command))
