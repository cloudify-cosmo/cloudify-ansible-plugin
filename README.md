cloudify-ansible-plugin
========================

The Ansible plugin can be used to run Ansible Playbooks or Modules during execution of a Cloudify Deployment. This plugin provides an agentless solution for configuration management.

Plugin Requirements:
 * Cloudify Manager
 * Python 2.7

Recommended:
 * Tested on Ubuntu images.

Current Functionality:
 - Installs and configures Ansible locally in the deploynent
 - Adds a host (ip or hostname) to a group. Creates a group if one does not already exist.
 - Uploads an Ansible Playbook to the manager (provided in the cwd during blueprint upload, or in a URL)
 - Runs an Ansible Playbook

