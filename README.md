cloudify-ansible-plugin
========================

Current Functionality:
 - Install Ansible on Manager
 - Add Playbook into manager
 - Add Hosts to Production Hosts File
 - Add Hosts to Staging Hosts File

Planned:
 - add ansible-playbook command to lifecyle implementation as well as optional arguments
 - Create Directory Structure recommended in best practices
 - Pull Information from Manager about existing nodes managed by cloudify
 - Create implementations for adding existing nodes to ansible
 -  - map node_types to ansible inventory types
 -  - map node properties to ansible inventory arguments
