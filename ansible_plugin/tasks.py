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
import os,subprocess

# ctx is imported and used in operations
from cloudify import ctx
from cloudify import exceptions
from cloudify.decorators import operation

# Runs any Shell Command
def _run_shell_command(command):
  ctx.logger.info("Running shell command: {0}".format(command))
  try:
    run = subprocess.check_call(
      command)
  except subprocess.CalledProcessError:
    ctx.logger.error("Unable to run shell command: {0}".format(command))
    raise NonRecoverableError("Command failed: {0}".format(command))
  return run

@operation
def run_playbook(path,arguments,**kwargs):

  '''
    runs a playbook
  '''

  command = ['ansible-playbook',path,arguments]

  ctx.logger.info("Running Playbook: [Shell Command]: {0}".format(command))

  _run_shell_command(command)

@operation
def download_playbook(playbook_file,target_file,**kwargs):

  '''
    adds a playbook file in /etc/ansible with content {entry}
  '''

  ctx.logger.debug('getting Playbook file...')

  try:
    blueprint,resource_path,log,target_path = ctx.download_resource(playbook_file,target_file)
  except Exception as e:
    raise exceptions.NonRecoverableError("Could not get '{0}' ({1}: {2})".format(playbook_file,type(e).__name__, e))

  ctx.logger.info("Blueprint: {0}, Log: {1}, Downloaded playbook file '{2}' to: {3}. ".format(blueprint,resource_path,log,target_path))

