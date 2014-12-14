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
# for finding out the linux distro
import sys,os,platform
# for downloading rpm/ppc files
import urllib

# ctx is imported and used in operations
from cloudify import ctx

# put the operation decorator on any function that is a task
from cloudify.decorators import operation

# Runs any Shell Command
def run_shell_command(command):
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

# Gets the Distrobution
def get_distro_version():
  info = platform.dist()
  distro = info[0]
  version = info[1]
  return distro,version

# Returns the Package Manager for the distrobution
def get_package_manager():
  package_manager = "apt-get"
  distro,version = get_distro_version()
  if distro == "Ubuntu":
    ctx.logger.info("{0} is the Linux distribution.".format(distro))
    package_manager = "apt-get"
  elif distro == "Centos":
    ctx.logger.info("{0} is the Linux distribution.".format(distro))
    package_manager = "yum"
  else:
    ctx.logger.error("Currently Operating System {0} is not supported".format(distro))
    exit(1)
  return package_manager

# Returns Install Arguments for a Package Manager
def install_args(package_manager):
  if package_manager == "apt-get":
    quiet_output = "-qq"
    assume_yes = "-y"
  if package_manager == "yum":
    quiet_output = "-q"
    assume_yes = "-y"
  return quiet_output,assume_yes

# Upgrade the Package Manager
def upgrade_package_manager(package_manager):
  q,y = install_args(package_manager)
  ctx.logger.info("Upgrading {0}".format(package_manager))
  command = ["sudo",package_manager,"upgrade",y,q]
  try:
    o,e = run_shell_command(command)
  except TypeError:
  	ctx.logger.info("No Errors were raised in Command: ".format(command))
 	pass
  return o,e


# Installs the EPEL Repo
def install_epel_repo():
  wget_url = "http://dl.fedoraproject.org/pub/epel/5/x86_64/"
  distro,version = get_distro_version()
  if version == "5*":
    rpm_version = "epel-release-5-4.noarch.rpm"
  elif version == "6*":
    rpm_version = "epel-release-6-8.noarch.rpm"
  elif version == "7*":
    rpm_version = "epel-release-7-1.noarch.rpm"
  else:
  	rpm_version = ""
  	ctx.logger.error("invalid version of CentOs: {0}".format(version))
  filename = os.path.join("/tmp",rpm_version)
  if not os.path.exists(filename):
    ctx.logger.info("Deleting Existing RPM file: {0}".format(filename))
    ctx.logger.info("Downloading EPEL RPM: {0}{1}".format(wget_url,rpm_version))
    urllib.urlretrieve(wget_url + rpm_version, filename)
  command = ["sudo","rpm","-Uvh","/tmp/" + rpm_version]
  try:
    o,e = run_shell_command(command)
  except TypeError:
  	ctx.logger.info("No Errors were raised in Command: ".format(command))
 	pass
  return o,e


# Installs the PPA repos
def install_ppa_repo():
  # Installs the Software Properties Common Dependency
  def install_dependency():
    command = ["sudo","apt-get","install","software-properties-common"]
    try:
      o,e = run_shell_command(command)
    except TypeError:
      ctx.logger.info("No Errors were raised in Command: ".format(command))
      pass
    return o,e
  o,e = install_dependency()
  command = ["sudo","apt-add-repository","ppa:ansible/ansible"]
  try:
    o,e = run_shell_command(command)
  except TypeError:
  	ctx.logger.info("No Errors were raised in Command: ".format(command))
 	pass
  return o,e

# Decides which repos to install
def add_repo(package_manager):
  ctx.logger.info("Installing Additional Repositories to {0}".format(package_manager))
  if package_manager == "yum":
    o,e = install_epel_repo()
  elif package_manager == "apt-get":
    o,e = install_ppa_repo()
  return o,e

# Updates a Package Manager
def update_package_manager(package_manager):
  add_repo(package_manager)
  ctx.logger.info("Updating {0}".format(package_manager))
  command = ["sudo",package_manager,"update"]
  try:
    o,e = run_shell_command(command)
  except TypeError:
  	ctx.logger.info("No Errors were raised in Command: ".format(command))
  	pass
  return o,e

# validate the installation
def validate_installation(package):
  ctx.logger.info("Validating {0}: ".format(package))
  command = [pakcage,"--version"]
  o,e = run_shell_command(command)
  if o:
    ctx.logger.info("Installation successful.")
  else:
    ctx.logger.error("Installation failed.")


# Installs a Package
@operation
def install_package(package_manager, package):
  ctx.logger.info("Installing {0}".format(package))
  q,y = install_args(package_manager)
  command = ["sudo",package_manager,"install",package,q,y]
  try:
    o,e = run_shell_command(command)
  except TypeError:
  	ctx.logger.info("No Errors were raised in Command: ".format(command))
 	  pass
  validate_installation(package)

