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

# Import Cloudify exception
from cloudify.exceptions import NonRecoverableError

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

# Gets the Distrobution
def _get_distro_version():
  info = platform.dist()
  distro = info[0]
  version = info[1]
  return distro,version

# Returns the Package Manager for the distrobution
def _get_package_manager():
  package_manager = "apt-get"
  distro,version = _get_distro_version()
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
def _install_args(package_manager):
  if package_manager == "apt-get":
    quiet_output = "-qq"
    assume_yes = "-y"
  if package_manager == "yum":
    quiet_output = "-q"
    assume_yes = "-y"
  return quiet_output,assume_yes

# Upgrade the Package Manager
def _upgrade_package_manager(package_manager):
  q,y = _install_args(package_manager)
  ctx.logger.info("Upgrading {0}".format(package_manager))
  command = ["sudo",package_manager,"upgrade",y,q,"-f"]
  _run_shell_command(command)

# Installs the EPEL Repo
def _install_epel_repo():
  wget_url = "http://dl.fedoraproject.org/pub/epel/5/x86_64/"
  distro,version = _get_distro_version()
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
  _run_shell_command(command)

# Installs the PPA repos
def _install_ppa_repo():
  # Installs the Software Properties Common Dependency
  def install_dependency():
    command = ["sudo","apt-get","install","software-properties-common"]
    _run_shell_command(command)
  command = ["sudo","apt-add-repository","ppa:ansible/ansible"]
  _run_shell_command(command)

# Decides which repos to install
def _add_repo(package_manager):
  ctx.logger.info("Installing Additional Repositories to {0}".format(package_manager))
  if package_manager == "yum":
    _install_epel_repo()
  elif package_manager == "apt-get":
    _install_ppa_repo()

# Updates a Package Manager
def _update_package_manager(package_manager):
  command = ["sudo","apt-get","clean"]
  _run_shell_command(command)
  _add_repo(package_manager)
  ctx.logger.info("Updating {0}".format(package_manager))
  command = ["sudo",package_manager,"update"]
  _run_shell_command(command)

# validate the installation
def _validate_installation(package):
  ctx.logger.info("Validating {0}: ".format(package))
  command = [pakcage,"--version"]
  code = _run_shell_command(command)
  if code > 0:
    ctx.logger.info("Installation was unsuccessful")
  else:
    ctx.logger.info("Installation was successful")

# Installs a Package
def install_package(package):
  package_manager = _get_package_manager()
  ctx.logger.info("Installing {0}".format(package))
  _update_package_manager(package_manager)
  _upgrade_package_manager(package_manager)
  q,y = _install_args(package_manager)
  command = ["sudo",package_manager,"install",package,q,y]
  _run_shell_command(command)
  _validate_installation(package)

@operation
def install(**kwargs):
  if "package_name" in kwargs:
    package = package_name
  else:
    package = "ansible"
  install_package(package)
