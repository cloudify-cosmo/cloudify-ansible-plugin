########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

# Built-in Imports
from os.path import join as joinpath
from subprocess import Popen, PIPE

# Third-party Imports

# Cloudify imports
from cloudify import ctx
# from cloudify.state import ctx_parameters as inputs
from cloudify.decorators import operation
from cloudify import exceptions


@operation
def run_playbook(playbook, hosts, **kwargs):
    """ Runs a playbook as part of a Cloudify lifecycle operation """

    ctx.logger.info('Running an Ansible Playbook.')

    playbook_path = get_playbook_path(playbook, ctx=ctx)

    inventory = get_inventory_path(hosts)

    command = ['ansible-playbook', playbook_path,
               ''.join('--inventory=', inventory)]

    ctx.logger.info('Running command: {}.'.format(command))

    output = run_command(command)

    ctx.logger.info('Command Output: {}.'.format(output))

    ctx.logger.info('Finished running the Ansible Playbook.')


def get_playbook_path(playbook, ctx):

    temp_file = joinpath('/tmp', ctx.instance.id, 'playbook.file')

    try:
        temp_file_path = ctx.download_resource(playbook, temp_file)
    except Exception as e:
        raise exceptions.NonRecoverableError(
            'Could not get playbook file: {}.'.format(str(e)))

    return temp_file_path


def get_inventory_path(hosts):

    with open('/tmp/inventory', 'a') as f:
        for host in hosts:
            f.write('{}\n'.format(host))

    f.close()

    return '/tmp/inventory'


def run_command(command):

    try:
        run = Popen(command, stdout=PIPE)
    except Exception as e:
        raise exceptions.NonRecoverableError(
            'Unable to run command. Error {}'.format(str(e)))

    try:
        output = run.communicate()
    except Exception as e:
        raise exceptions.NonRecoverableError(
            'Unable to run command. Error {}'.format(str(e)))

    if run.returncode != 0:
        raise exceptions.NonRecoverableError(
            'Non-zero returncode. Output {}.'.format(output))

    return output
