cloudify-ansible-plugin
========================

The Ansible plugin can be used to run Ansible Playbooks or Modules during execution of a Cloudify Deployment. This plugin provides an agentless solution for configuration management.

Plugin Requirements:
 * Cloudify Manager
 * Python 2.7

Recommended:
 * Ubuntu

What it does:
 - Installs and configures Ansible locally in the deploynent
 - Adds a host (ip or hostname) to a group. Creates a group if one does not already exist.
 - Uploads an Ansible Playbook to the manager (provided in the blueprint directory.)
 - Runs an Ansible Playbook

