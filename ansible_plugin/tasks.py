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

# for running shell commands
import subprocess
import sys

# ctx is imported and used in operations
from cloudify import ctx
from cloudify.decorators import operation

# for handling files
from shutil import copy
from os import makedirs
from os.path import join as joinpath
from os.path import exists as pathexists
import os


@operation
def run_playbook(agent_key, user_home='/home/ubuntu/',
                 inventory='hosts', playbook='playbook.yml',
                 **kwargs):

    deployment_home = joinpath(user_home, '{0}{1}'
                               .format('cloudify.', ctx.deployment.id))
    playbook_binary = joinpath(deployment_home,
                               'env', 'bin', 'ansible-playbook')

    _run_playbook(playbook_binary, agent_key, user_home, inventory, playbook)


def _run_playbook(playbook_binary, agent_key, user_home='/home/ubuntu/',
                  inventory='hosts', playbook='playbook.yml'):

    command = [playbook_binary, '--sudo', '-i',
               inventory, playbook, '--private-key', agent_key]

    ctx.logger.info('Running playbook: {0}.'.format(playbook))

    run_shell_command(command)


@operation
def add_host(host, group, inventory, **kwargs):

    group = '[{0}]\n'.format(group)
    host = '{0}\n'.format(host)

    _add_host(host, group, inventory)


def _add_host(host, group, inventory):
    """if the group already exists in the inventory,
    the host will be added and add_line_to_location will
    return True. Otherwise, the group is added and the host under it
    """

    if add_to_location(os.getcwd(), inventory, group, host):
        ctx.logger.info('Added new host {0} under {1} in {2}.'
                        .format(host, group, inventory))
    else:
        new_line = '{0}{1}'.format(group, host)
        write_to_file(os.getcwd(), inventory, new_line)
        ctx.logger.info('Added new host {0} under {1} in {2}.'
                        .format(host, group, inventory))


def add_to_location(path, filename, search_string, string):
    """ Find search_string in file and write string directrly
        below it.
    """

    success = False
    new_file = joinpath('/tmp', filename)
    old_file = joinpath(path, filename)

    with open(new_file, 'w') as outfile:
        try:
            with open(old_file, 'r') as lines:
                for line in lines:
                    if line == search_string:
                        outfile.write(line)
                        outfile.write(string)
                        success = True
                    else:
                        outfile.write(line)

            lines.close()
        except IOError:
            success = False

    outfile.close()

    if success is True:
        copy(new_file, old_file)
        return success
    else:
        return success


def write_to_file(path, filename, entry):

    if not pathexists(path):
        makedirs(path)

    path_to_file = joinpath(path, filename)

    if not pathexists(path_to_file):
        try:
            f = open(path_to_file, 'w')
            f.write(entry)
        except IOError as e:
            ctx.logger.error('Can\'t open file {0} for writing: {1}'
                             .format(path_to_file, e))
    else:
        try:
            f = open(path_to_file, 'a')
            f.write(entry)
        except IOError as e:
            ctx.logger.error('Can\'t open file {0} for writing: {1}'
                             .format(path_to_file, e))
        f.close()


def run_shell_command(command):
    """this runs a shell command.
    """
    ctx.logger.info('Running shell command: {0}'
                    .format(command))

    try:
        run = subprocess.Popen(command, stdout=subprocess.PIPE)
        output, error = run.communicate()
        if output:
            ctx.logger.info('output: {0}'.format(output))
        elif error:
            ctx.logger.error('error: {0}'.format(error))
            raise Exception('{0} returned {1}'.format(command, error))
    except:
        e = sys.exc_info()[0]
        ctx.logger.error('command failed: {0}, exception: {1}'
                         .format(command, e))
        raise Exception('{0} returned {1}'.format(command, e))
