cloudify-ansible-plugin
========================

The Ansible plugin can be used to run Ansible Playbooks or Modules during execution of a Cloudify Deployment. This plugin provides an agentless solution for configuration management.

Plugin Requirements:
 * Cloudify Manager
 * Python 2.7

Recommended:
 * Tested on Ubuntu.

Current Functionality:
 - Installs and configures Ansible locally in the deploynent
 - Adds a host (ip or hostname) to a group. Creates a group if one does not already exist.
 - Uploads an Ansible Playbook to the manager (provided in the cwd during blueprint upload, or in a URL)
 - Runs an Ansible Playbook

For a pre-configured blueprint and inputs file go to tests/blueprints.

Operations in the tasks module and their inputs:
run_playbook
 inputs:
  * ansible_home is a path to the ansible etc directory
  * inventory is the name of the file containing the list of hosts that need the playbook applied to them
  * a playbook identified by key "local\_file" or "playbook_url"

get_playbook(**kwargs):
 inputs:
  * ansible_home is a path to the ansible etc directory
  * a playbook identified by key "local\_file" or "playbook_url"

add_host_to_group(host, group, inventory, **kwargs):
 inputs:
  * the host, probably a floating ip address
  * the name of a group if you are giving multiple hosts
  * inventory is the name of the file containing the list of hosts that need the playbook applied to them
  * a playbook identified by key "local\_file" or "playbook_url"
