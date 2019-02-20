# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
from tempfile import mkdtemp
from uuid import uuid1
import yaml

from cloudify.exceptions import NonRecoverableError
try:
    from cloudify.constants import RELATIONSHIP_INSTANCE
except ImportError:
    RELATIONSHIP_INSTANCE = 'relationship-instance'

from cloudify_ansible.constants import (
    BP_INCLUDES_PATH,
    WORKSPACE,
    SOURCES
)


def handle_key_data(_data, workspace_dir):
    """Take Key Data from ansible_ssh_private_key_file and
    replace with a temp file.

    :param _data: The hosts dict (from YAML).
    :param workspace_dir: The temp dir where we are putting everything.
    :return: The hosts dict with a path to a temp file.
    """

    def recurse_dictionary(existing_dict, key='ansible_ssh_private_key_file'):
        if key not in existing_dict:
            for k, v in existing_dict.items():
                if isinstance(v, dict):
                    existing_dict[k] = recurse_dictionary(v)
        elif key in existing_dict:
            private_key_file = os.path.join(workspace_dir, str(uuid1()))
            with open(private_key_file, 'w') as outfile:
                outfile.write(existing_dict[key])
            os.chmod(private_key_file, 0o600)
            existing_dict[key] = private_key_file
        return existing_dict

    return recurse_dictionary(_data)


def handle_file_path(file_path, _ctx):
    """Get the path to a file.

    I do this for two reasons:
      1. The Download Resource only downloads an individual file.
      Ansible Playbooks are often many files.
      2. I have not figured out how to pass a file as an in
      memory object to the PlaybookExecutor class.

    :param file_path: The `site_yaml_path` from `run`.
    :param _ctx: The Cloudify Context.
    :return: The absolute path on the manager to the file.
    """

    if not isinstance(file_path, basestring):
        raise NonRecoverableError(
            'The variable file_path {0} is a {1},'
            'expected a string.'.format(file_path, type(file_path)))
    if not getattr(_ctx, '_local', False):
        file_path = \
            BP_INCLUDES_PATH.format(
                tenant=_ctx.tenant_name,
                blueprint=_ctx.blueprint.id,
                relative_path=file_path)
    if os.path.exists(file_path):
        return file_path
    raise NonRecoverableError(
        'File path {0} does not exist.'.format(file_path))


def handle_site_yaml(site_yaml_path, _ctx):
    """ Create an absolute local path to the site.yaml.

    :param site_yaml_path: Relative to the blueprint.
    :param _ctx: The Cloudify context.
    :return: The final absolute path on the system to the site.yaml.
    """

    site_yaml_real_path = os.path.abspath(
        handle_file_path(site_yaml_path, _ctx))
    site_yaml_real_dir = os.path.dirname(site_yaml_real_path)
    site_yaml_real_name = os.path.basename(site_yaml_real_path)
    site_yaml_new_dir = os.path.join(
        _ctx.instance.runtime_properties[WORKSPACE], 'playbook')
    shutil.copytree(site_yaml_real_dir, site_yaml_new_dir)
    site_yaml_final_path = os.path.join(site_yaml_new_dir, site_yaml_real_name)
    with open(site_yaml_final_path, 'r') as infile:
        _ctx.logger.debug('Contents site.yaml:\n {0}'.format(infile.read()))
    return site_yaml_final_path


def handle_sources(data, site_yaml_abspath, _ctx):
    """Allow users to provide a path to a hosts file
    or to generate hosts dynamically,
    which is more comfortable for Cloudify users.

    :param data: Either a dict (from YAML)
        or a path to a conventional Ansible file.
    :param site_yaml_abspath: This is the path to the site yaml folder.
    :param _ctx: The Cloudify context.
    :return: The final path of the hosts file that
        was either provided or generated.
    """

    hosts_abspath = os.path.join(os.path.dirname(site_yaml_abspath), 'hosts')
    if isinstance(data, dict):
        data = handle_key_data(
            data, _ctx.instance.runtime_properties[WORKSPACE])
        if os.path.exists(hosts_abspath):
            _ctx.logger.error(
                'Hosts data was provided but {0} already exists. '
                'Overwriting existing file.'.format(hosts_abspath))
        with open(hosts_abspath, 'w') as outfile:
            _ctx.logger.info(
                'Writing this data to temp file: {0}'.format(data))
            yaml.dump(data, outfile, default_flow_style=False)
    with open(hosts_abspath, 'r') as infile:
        _ctx.logger.debug('Contents hosts:\n {0}'.format(infile.read()))
    return hosts_abspath


def create_playbook_workspace(ctx):
    """ Create a temporary folder, so that we don't overwrite fields.

    :param ctx: The Cloudify context.
    :return:
    """

    ctx.instance.runtime_properties[WORKSPACE] = mkdtemp()


def delete_playbook_workspace(ctx):
    """Delete the temporary folder.

    :param ctx: The Cloudify context.
    :return:
    """

    directory = ctx.instance.runtime_properties.get(WORKSPACE)
    if directory and os.path.exists(directory):
        shutil.rmtree(directory)


def get_source_config_from_ctx(_ctx,
                               group_name=None,
                               hostname=None,
                               host_config=None):

    """Generate a source config from CTX.

    :param _ctx: Either a NodeInstance or a RelationshipInstance ctx.
    :param group_name: User's override value, like 'webservers'.
    :param hostname: User's override value, like 'web'.
    :param host_config: User's override value. Like:
       {
           'ansible_host': '127.0.0.1',
           'ansible_user': 'ubuntu',
       }
    :return:
    """

    if _ctx.type == RELATIONSHIP_INSTANCE:
        host_config = host_config or \
            get_host_config_from_compute_node(_ctx.target)
        group_name, hostname = \
            get_group_name_and_hostname(_ctx.target, group_name, hostname)
    else:

        if 'cloudify.nodes.Compute' not in _ctx.node.type_hierarchy and \
                _ctx.instance.runtime_properties.get(SOURCES, {}):
            return _ctx.instance.runtime_properties[SOURCES]
        host_config = host_config or \
            get_host_config_from_compute_node(_ctx)
        group_name, hostname = \
            get_group_name_and_hostname(_ctx, group_name, hostname)
    return {
        group_name: {
            'hosts': {
                hostname: host_config
            }
        }
    }


def get_group_name_and_hostname(_ctx, group_name=None, hostname=None):
    """We allow a user to extend the `cloudify.nodes.Compute` node type
    and use that as a host group name in Ansible.

    :param _ctx: Either a NodeInstance or a RelationshipInstance ctx.
    :param group_name: User's override value.
    :param hostname: User's override value.
    :return:
    """

    if not group_name and not hostname and \
            'cloudify.nodes.Compute' not in _ctx.node.type_hierarchy:
        raise NonRecoverableError(
            'No sources or group_name, or hostname was provided, '
            'and furthermore no compute node was provided '
            'to generate them from.'
        )
    group_name = group_name or _ctx.node.type
    hostname = hostname or _ctx.instance.id
    return group_name, hostname


def get_host_config_from_compute_node(_ctx):
    return {
        'ansible_host': _ctx.instance.runtime_properties.get(
            'ip', _ctx.node.properties.get('ip')),
        'ansible_user': _ctx.node.properties.get(
            'agent_config', {}).get('user'),
        'ansible_ssh_private_key_file':
            _ctx.node.properties.get('agent_config', {}).get('key'),
        'ansible_ssh_common_args': '-o StrictHostKeyChecking=no',
        'ansible_become': True
    }
