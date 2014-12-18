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
import os.path as ospath
from os import makedirs


def _run_shell_command(command):
    """this runs a shell command.
    """

    ctx.logger.info("Running shell command: {0}"
                    .format(command))
    try:
        run = subprocess.check_call(command)
    except subprocess.CalledProcessError:
        ctx.logger.error("Unable to run shell command: {0}"
                         .format(command))
        raise NonRecoverableError("Command failed: {0}"
                                  .format(command))
    return run


@operation
def run_playbook(path, arguments, **kwargs):
    """runs a playbook
    """

    command = ['ansible-playbook', path, arguments]

    ctx.logger.info("Running Playbook: [Shell Command]: {0}"
                    .format(command))

    _run_shell_command(command)


@operation
def get_playbook(target_file, **kwargs):
    """adds a playbook file in /etc/ansible with content {entry}
    """

    if 'playbook_url' in kwargs:
        url = kwargs['playbook_url']
        ctx.logger.debug('getting Playbook file...')
        status = _download_file(url, target_file)
        if status == 0:
            ctx.logger.info(
                "Downloaded blueprint from url: {0}"
                .format(url))
        else:
            ctx.logger.error(
                "Unable to download blueprint from url: {0}"
                .format(url))
    elif 'local_file' in kwargs:
        file = kwargs['local_file']
        status = _copy_file(file, target_file)
    else:
        ctx.logger.error("No valid file path or url provided.")


def _download_file(url, target_file):
    """ downloads a file from a url and places it in the requested directory
    """

    req = Request(url)

    try:

        file = urlopen(req)
        with open(target_file, 'wb') as local_file:
            data = file.read()
            local_file.write(data)
            local_file.close()

    except HTTPError, e:
        print('HTTPError {0} {1}'.format(e.code, url))
        raise exceptions.NonRecoverableError(
            'Could not get "{0}" ({1}: {2})'.format(
                url, type(e).__name__, e))
        return False

    except URLError, e:
        print('URLError {0} {1}'.format(e.reason, url))
        raise exceptions.NonRecoverableError(
            'Could not get "{0}" ({1}: {2})'.format(
                url, type(e).__name__, e))
        return False


def _copy_file(file, target_file):
    """ copies 'file' from local machine and moves to
        target_file
    """

    try:
        copy(file, target_file)

    except Error as e:
        print('Error {0}'.format(e))
        raise exceptions.NonRecoverableError(
            'Could not get "{0}" ({1}: {2})'.format(
                file, type(e).__name__, e))
        return False

    return True


@operation
def add_host_to_group(host, group, inventory, **kwargs):
    """
        this puts a host under a group in inventory file
    """

    if 'ansible_home' in kwargs:
        ansible_home = kwargs['ansible_home']
    else:
        ansible_home = '/home/ubuntu/ansible'

    group = '[' + group + ']\n'
    host = host + '\n'
    if _add_to_location(ansible_home, inventory, group, host):
        """
            if the group already exists in the inventory,
            the host will be added and add_line_to_location will
            return True. Otherwise, the group is added and the host under it
        """
        print("Added new host {0} under {1} in {2}."
              .format(host, group, inventory))
    else:
        new_line = group + host
        _write_to_file(ansible_home, inventory, new_line)
        print("""Added new host {0} under {1} in new file {2}."""
              .format(host, group, inventory))


def _add_to_location(path, filename, search_string, string):
    """ Find search_string in file and write string directrly
        below it.
    """

    success = False
    new_file = ospath.join('/tmp', filename + ".temp")
    old_file = ospath.join(path, filename)

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


def _write_to_file(path, filename, entry):
    """ writes a entry to a file
    """
    if not ospath.exists(path):
        makedirs()
    path_to_file = ospath.join(path, filename)
    if not ospath.exists(path_to_file):
        f = open(path_to_file, 'w')
        f.write(entry)
    else:
        f = open(path_to_file, 'a')
        f.write(entry)
    f.close()


@operation
def run_ansible(**kwargs):
    """ Makes an API call to Ansible Runner.
        For a list of possible arguments, see:
        https://github.com/ansible/ansible/
        blob/devel/lib/ansible/runner/__init__.py
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
