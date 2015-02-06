cloudify-ansible-plugin
========================

The Ansible plugin can be used to run Ansible Playbooks against a single node in a Cloudify Blueprint.

Plugin Requirements:
 * Python 2.7

Tested on:
 * Ubuntu

How to use it:

In your blueprint directory include the playbook that you want to run.

    $ ls
    blueprint.yaml  playbook.yaml 

Import the plugin.yaml file in your Cloudify Blueprint:

    imports:
      - https://raw.githubusercontent.com/EarthmanT/cloudify-ansible-plugin/master/plugin.yaml

Create node type with a configure and a create lifecycle operation. Map them to the configure and ansible_playbook functions in the tasks module.

node_types:

  ansible.nodes.Application:
    derived_from: cloudify.nodes.ApplicationModule
    interfaces:
      cloudify.interfaces.lifecycle:
        configure:
          implementation: ansible.ansible_plugin.tasks.configure
          inputs: {}
        start:
          implementation: ansible.ansible_plugin.tasks.ansible_playbook
          inputs: {}

Then create a node_template of that node type. Make sure that there are user and keypair inputs to your configure operation, and that there are playbook and private_ip_address inputs to your create operation.

Add a reference to the playbook file in the node_template.

     application_configure:
      type: ansible.nodes.Application
      interfaces:
        cloudify.interfaces.lifecycle:
          configure:
            implementation: ansible.ansible_plugin.tasks.configure
            inputs:
              user: { get_input: agent_user }
              keypair: { get_input: key_name }
          start:
            implementation: ansible.ansible_plugin.tasks.ansible_playbook
            inputs:
              playbook: { get_input: playbook_file }
              private_ip_address: { get_attribute: [ host, ip ] }
 
See the working example for more detail.
