cloudify-ansible-plugin
========================

The Ansible plugin can be used to run Ansible Playbooks against a single node in a Cloudify Blueprint.

Plugin Requirements:
 * Python 2.7

Tested on:
 * Ubuntu

How to use it:

Import the plugin.yaml file in your Cloudify Blueprint:

    imports:
      - https://raw.githubusercontent.com/EarthmanT/cloudify-ansible-plugin/master/plugin.yaml

Create node that inherits the ansible.nodes.Application node type. In your blueprint directory include the playbook that you want to run.

    $ ls
    blueprint.yaml	playbook.yaml	

Add a reference to that file in the node_template for the application layer that you will configure with Ansible. Add the private ip address for the host that you want to run the playbook against.

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
