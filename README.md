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

How to make sure that Ansible is installed on the manager:
Ansible is installed per deployment. This keeps your file system organized. It also emphasizes the nature pluggable nature of the plugin.

In your blueprint, create a node. I use cloudify.nodes.ApplicationModule. Add the configure lifecycle operation, and map to the configuration method.

  ansible_configuration:
    type: cloudify.nodes.ApplicationModule
    interfaces:
      cloudify.interfaces.lifecycle:
        configure:
          implementation: cloudify-ansible-plugin.ansible_plugin.configure.configure

How to use the Ansible Plugin:



There are four operations: add_host_to_group, get_playbook, and run_playbook.

add_host_to_group(host, group, inventory, **kwargs)
 inputs:
  * the host, probably a floating ip address
  * the name of a group if you are giving multiple hosts
  * inventory is the name of the file containing the list of hosts that need the playbook applied to them
  * a playbook identified by key "local\_file" or "playbook_url"

  add_host_to_group:
    type: cloudify.nodes.ApplicationModule
    interfaces:
      cloudify.interfaces.lifecycle:
        configure:
          implementation: cloudify-ansible-plugin.ansible_plugin.tasks.add_host_to_group
          inputs:
            host: { get_attribute: [ new_host, ip ] }
            group: { get_input : test_group_name }
            inventory: { get_input : test_inventory_name }
    relationships:
      - type: cloudify.relationships.depends_on
        target: ansible_configuration
      - type: cloudify.relationships.depends_on
        target: virtual_ip

get_playbook(**kwargs):
 inputs:
  * ansible_home is a path to the ansible etc directory
  * a playbook identified by key "local\_file" or "playbook_url"

  ansible_playbook:
    type: cloudify.nodes.ApplicationModule
    interfaces:
      cloudify.interfaces.lifecycle:
        create:
          implementation: cloudify-ansible-plugin.ansible_plugin.tasks.get_playbook
          inputs:
            local_file: { get_input : where_to_get_the_playbook } # or local_file to a file in the local directory
    relationships:
      - type: cloudify.relationships.depends_on
        target: ansible_configuration
      - type: cloudify.relationships.depends_on
        target: new_host
      - type: cloudify.relationships.depends_on
        target: add_host_to_group

run_playbook
 inputs:
  * ansible_home is a path to the ansible etc directory
  * inventory is the name of the file containing the list of hosts that need the playbook applied to them
  * a playbook identified by key "local\_file" or "playbook_url"

  run_playbook:
    type: cloudify.nodes.ApplicationModule
    interfaces:
      cloudify.interfaces.lifecycle:
        create:
          implementation: cloudify-ansible-plugin.ansible_plugin.tasks.run_playbook
          inputs:
            local_file: { get_input : where_to_get_the_playbook } # or local_file to a file in the local directory
            agent_key: { get_input : agent_key_path }
    relationships:
      - type: cloudify.relationships.depends_on
        target: ansible_configuration
      - type: cloudify.relationships.depends_on
        target: ansible_playbook

