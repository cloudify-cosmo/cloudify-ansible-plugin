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
# for walking files and directories
import os

# ctx is imported and used in operations
from cloudify import ctx

# put the operation decorator on any function that is a task
from cloudify.decorators import operation

ansible_home = "/etc/ansible"

def _write_to_file(path,filename,entry):
  if not os.path.exists(path):
    os.makedirs()
  path_to_file = os.path.join(path,filename)
  if not os.path.exists(path_to_file):
    f = open(path_to_file,"w")
    f.write(entry)
  else:
    f = open(path_to_file,"a")
    f.write(entry)
  f.close()

# Runs the Shell Command
def _run_shell_command(command):
  ctx.logger.info("Running shell command: {0}".format(command))
  try:
    run = subprocess.Popen(
      command, 
      stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE, 
      stdin=subprocess.PIPE)
  except ValueError:
    print ValueError
    ctx.logger.error("Invalid Shell Command: {0}".format(command))
  standard_output, standard_error = run.communicate()
  return standard_output, standard_error

@operation
def add_production_host(host,address):
  '''
    this adds a production host address line to the production hosts file in /etc/ansible
    in the near future, we will modify to handle updating a host or removing a host, as well as group, variable and role management
  '''
  entry = host,address
  _write_to_file(ansible_home,"production",entry)

@operation
def add_playbook(playbook,entry):
  '''
    adds a {playbook}.yml file in /etc/ansible with content {entry}
  '''
  _write_to_file(ansible_home,playbook,entry)
