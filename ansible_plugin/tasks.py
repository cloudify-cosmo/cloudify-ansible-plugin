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

ansible_home = "/etc/ansible/"

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

def _search_file_string(path,filename,string):
  thefile = os.path.join(path,filename)
  with open(thefile) as search:
    for line in search:
      line = line.rstrip()
      if line == string:
        return True
      else:
        return False

def add_line_to_location(path,filename,line,string):
  success = False
  new_file = os.path.join('/tmp',filename+".temp")
  old_file = os.path.join(path,filename)
  with open(new_file,'w') as outfile:
    try:
      with open(old_file,'r') as infile:
        rows = iter(infile)
        for row in rows:
          if row == line:
            outfile.write(row)
            outfile.write(new_line)
            success = True
          else:
            outfile.write(row)
      infile.close()
    except IOError as e:
      success = False
  outfile.close()
  if success == True:
    shutil.copyfile(new_file,old_file)
    return success
  else:
    return success

@operation
def add_host_to_inventory(name,group,inventory,**kwargs):
  '''
    this adds a host role, which may be a geographic or application or contextual role, to the specified inventory (staging, production).
  '''
  if _search_file_string(ansible_home,inventory,name):
    ctx.logger.error("Unable to add {0} to {1}. Host already exists in this inventory.".format(name,inventory))
  else:
    _write_to_file(ansible_home,inventory,name)

@operation
def add_host_to_group(name,group,inventory,**kwargs):
  '''
    this puts a host under a group in inventory file
  '''
  group = "\n[" + group + "]\n"
  name = name + '\n'
  if add_line_to_location(ansible_home,inventory,group,name):
    '''
      if the group already exists in the inventory, the host will be added and add_line_to_location will return True. Otherwise, the group is added and the host under it
    '''
    ctx.logger.info("Added new host {0} under {1} in {2}.".format(name,group,inventory))
  else:
    new_line = group + name
    _write_to_file(ansible_home,inventory,new_line)
    ctx.logger.info("Added new host {0} under {1} in new file {2}.".format(name,group,inventory))

@operation
def add_playbook(client_path,ansible_home):
  '''
    adds a playbook file in /etc/ansible with content {entry}
  '''
  path = ctx.downloadresource(client_path,ansible_home)
  ctx.logger.info("Added file: {0}".format(path))

def run_playbook(playbook,**kwargs):
  '''
    runs ad-hoc command. provide existing ansible_playbook and any arguments,
    i.e. alternative module directories (--module-path,"/usr/share/ansible")
    i.e. alternative inventory hosts file (--inventory, "/usr/share/ansible/hosts")
  '''
  command = ["ansible_playbook",playbook]
  for key,value in kwargs.iteritems():
    command.append(key)
    command.append(value)
  _run_shell_command(command)