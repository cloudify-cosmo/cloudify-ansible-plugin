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
from cloudify import exceptions
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

# for ansible api
import ansible.runner

# for handling files
from urllib2 import Request, urlopen, URLError, HTTPError
from shutil import copy, Error
from os.path import basename
from os import makedirs
from os.path import join as joinpath
from os.path import exists as pathexists
import os


@operation
def run_playbook(
    host, group, inventory, agent_key,
    local_file, user_home='/home/ubuntu',
        **kwargs):
    """runs a playbook, use cloudify.interfaces.lifecycle.start

    """

    deployment_home = joinpath(user_home, 'cloudify.', ctx.deployment.id)
    etc_ansible = joinpath(deployment_home, 'env', 'etc', 'ansible')
    ansible_binary = joinpath(deployment_home, 'env', 'bin',
                              'ansible-playbook')

    add_host(etc_ansible, host, group, inventory)

    get_playbook(etc_ansible, local_file)

    path_to_playbook = joinpath(etc_ansible, local_file)
    path_to_inventory = joinpath(etc_ansible, inventory)

    command = [ansible_binary, '--sudo', '-i',
               path_to_inventory, path_to_playbook,
               '--private-key', agent_key]

    run_shell_command(command)


@operation
def get_playbook(etc_ansible, local_file, **kwargs):
    """adds a playbook file in .../etc/ansible with content {entry}
       use: cloudify.interfaces.lifecycle.configure
    """

    target_file = joinpath(etc_ansible, basename(local_file))
    ctx.download_resource(local_file, target_file)


@operation
def add_host(etc_ansible, host, group, inventory, **kwargs):
    """
        this puts a host under a group in inventory file
        use: cloudify.interfaces.lifecycle.configure
    """

    group = '[' + group + ']\n'
    host = host + '\n'

    if add_to_location(etc_ansible, inventory, group, host):
        """
            if the group already exists in the inventory,
            the host will be added and add_line_to_location will
            return True. Otherwise, the group is added and the host under it
        """
        print("Added new host {0} under {1} in {2}."
              .format(host, group, inventory))
    else:
        new_line = group + host
        write_to_file(etc_ansible, inventory, new_line)
        print("""Added new host {0} under {1} in new file {2}."""
              .format(host, group, inventory))


def add_to_location(path, filename, search_string, string):
    """ Find search_string in file and write string directrly
        below it.
    """

    success = False
    new_file = joinpath('/tmp', filename + ".temp")
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


def replace_string(file, old_string, new_string):

    new_file = joinpath('/tmp', file)

    try:
        with open(new_file, 'wt') as fout:
            try:
                with open(file, 'rt') as fin:
                    for line in fin:
                        fout.write(line.replace(old_string, new_string))
            except IOError:
                raise NonRecoverableError('Unabled to open file {0}.'
                                          .format(file))
    except IOError:
        raise NonRecoverableError('Unabled to open temporary file {0}.'
                                  .format(new_file))

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


@operation
def run_ansible(**kwargs):
    """ Makes an API call to Ansible Runner.
        For a list of possible arguments, see:
        https://github.com/ansible/ansible/
        blob/devel/lib/ansible/runner/__init__.py
        use cloudify.interfaces.lifecycle.start
    """
    ctx.logger.info("running ansible: ")
    del kwargs['ctx']
    runner = ansible.runner.Runner(**kwargs)
    results = runner.run()
    _log_results(results)


def _log_results(results):
    for (hostname, result) in results['contacted'].items():
        if not 'failed' in result:
            ctx.logger.info('{0} >>>> {1}'.format(hostname, result))
        elif 'failed' in result:
            ctx.logger.error('{0} >>>> {1}'.format(hostname, result))
    for (hostname, result) in results['dark'].items():
        ctx.logger.error('{0} >>>>> {1}'.format(hostname, result))


def run_shell_command(command):
    """this runs a shell command.
    """
    ctx.logger.info("Running shell command: {0}"
                    .format(command))

    try:
        run = subprocess.Popen(command, stdout=subprocess.PIPE)
        output, error = run.communicate()
        if output:
            for lines in output:
                ctx.logger.info('lines: {0}'.format(lines))
        elif error:
            ctx.logger.error('error: {0}'.format(error))
            raise Exception('{0} returned {1}'.format(command, error))
    except:
        e = sys.exc_info()[1]
        ctx.logger.error('error: {0}'.format(e))
