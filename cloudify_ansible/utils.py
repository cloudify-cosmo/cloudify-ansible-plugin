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
import re
import sys
import json
import yaml
import errno
import shutil
from uuid import uuid1
from copy import deepcopy
from tempfile import mkdtemp

from cloudify import ctx
from ansible.playbook import Playbook
from cloudify.manager import get_rest_client
from ansible.vars.manager import VariableManager
from ansible.parsing.dataloader import DataLoader
from cloudify_common_sdk.utils import get_deployment_dir, get_node_instance_dir
from cloudify_rest_client.constants import VisibilityState
from cloudify.utils import LocalCommandRunner
from cloudify_ansible_sdk._compat import (
    text_type, urlopen, URLError)
from cloudify.exceptions import (NonRecoverableError,
                                 OperationRetry,
                                 HttpException,
                                 CommandExecutionException)
from script_runner.tasks import (
    ILLEGAL_CTX_OPERATION_ERROR,
    UNSUPPORTED_SCRIPT_FEATURE_ERROR
)

from cloudify_ansible.constants import (
    COMPLETED_TAGS,
    AVAILABLE_TAGS,
    ANSIBLE_TO_INSTALL,
    BP_INCLUDES_PATH,
    INSTALLED_PACKAGES,
    INSTALLED_COLLECTIONS,
    INSTALLED_ROLES,
    LOCAL_VENV,
    PLAYBOOK_VENV,
    WORKSPACE,
    SOURCES,
    HOSTS
)
from cloudify_ansible_sdk.sources import AnsibleSource


runner = LocalCommandRunner()

try:
    from cloudify.proxy.client import ScriptException
except ImportError:
    ScriptException = Exception


try:
    from cloudify.constants import RELATIONSHIP_INSTANCE, NODE_INSTANCE
except ImportError:
    NODE_INSTANCE = 'node-instance'
    RELATIONSHIP_INSTANCE = 'relationship-instance'


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
            # If is_file_path is True, this has already been done.
            try:
                is_file_path = os.path.exists(existing_dict[key])
            except TypeError:
                is_file_path = False
            if not is_file_path:
                private_key_file = os.path.join(workspace_dir, str(uuid1()))
                with open(private_key_file, 'w') as outfile:
                    if isinstance(existing_dict[key], (dict, list)):
                        existing_dict[key] = json.dumps(existing_dict[key])
                    outfile.write(existing_dict[key])
                os.chmod(private_key_file, 0o600)
                existing_dict[key] = private_key_file
        return existing_dict
    return recurse_dictionary(_data)


def download_nested_file_to_new_nested_temp_file(file_path, new_root, _ctx):
    """ Download a file to a similar folder system with a new root directory.

    :param file_path: Basically the resource path for download resource source.
    :param new_root: Like a temporary directory
    :param _ctx:
    :return:
    """

    dirname, file_name = os.path.split(file_path)
    # Create the new directory path including the new root.
    new_dir = os.path.join(new_root, dirname)
    new_full_path = os.path.join(new_dir, file_name)
    try:
        os.makedirs(new_dir)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(new_dir):
            pass
        else:
            raise
    return _ctx.download_resource(file_path, new_full_path)


def _get_tenant_name(_ctx=None):
    _ctx = _ctx or ctx
    client = get_rest_client()
    blueprint_from_rest = client.blueprints.get(_ctx.blueprint.id)
    if blueprint_from_rest['visibility'] == VisibilityState.GLOBAL:
        return blueprint_from_rest['tenant_name']
    return _ctx.tenant_name


def _get_collections_location(_ctx=None):
    _ctx = _ctx or ctx
    runtime_properties = get_instance(ctx).runtime_properties
    if not is_local_venv() and \
            (get_node(ctx).properties.get('galaxy_collections')
             or runtime_properties.get('galaxy_collections')):
        return runtime_properties.get(WORKSPACE)
    return os.path.join(runtime_properties.get(PLAYBOOK_VENV),
                        'lib',
                        'python' + sys.version[:3],
                        'site-packages'
                        )


def _get_roles_location(_ctx=None):
    _ctx = _ctx or ctx
    runtime_properties = get_instance(ctx).runtime_properties
    roles_location = os.path.join(runtime_properties.get(WORKSPACE), 'roles')
    if not os.path.exists(roles_location):
        os.mkdir(roles_location)
    return roles_location


def handle_file_path(file_path, additional_playbook_files, _ctx):
    """Get the path to a file.

    I do this for two reasons:
      1. The Download Resource only downloads an individual file.
      Ansible Playbooks are often many files.
      2. I have not figured out how to pass a file as an in
      memory object to the PlaybookExecutor class.

    :param file_path: The `site_yaml_path` from `run`.
    :param additional_playbook_files: additional files
      adjacent to the playbook path.
    :param _ctx: The Cloudify Context.
    :return: The absolute path on the manager to the file.
    """

    def _get_deployment_blueprint(deployment_id):
        try:
            # get the latest deployment update to get the new blueprint id
            client = get_rest_client()
            dep_upd = \
                client.deployment_updates.list(deployment_id=deployment_id,
                                               sort='created_at')[-1]
            return client.deployment_updates.get(
                dep_upd.id)["new_blueprint_id"]
        except KeyError:
            raise NonRecoverableError(
                "can't get blueprint for deployment {0}".format(deployment_id))

    if not isinstance(file_path, (text_type, bytes)):
        raise NonRecoverableError(
            'The variable file_path {0} is a {1},'
            'expected a string.'.format(file_path, type(file_path)))
    if not getattr(_ctx, '_local', False):
        if additional_playbook_files:
            # This section is intended to handle scenario where we want
            # to download the resource instead of use absolute path.
            # Perhaps this should replace the old way entirely.
            # For now, the important thing here is that we are
            # enabling downloading the playbook to a remote host.
            playbook_file_dir = mkdtemp()
            new_file_path = download_nested_file_to_new_nested_temp_file(
                file_path,
                playbook_file_dir,
                _ctx
            )
            for additional_file in additional_playbook_files:
                download_nested_file_to_new_nested_temp_file(
                    additional_file,
                    playbook_file_dir,
                    _ctx
                )
            return new_file_path
        else:
            # handle update deployment different blueprint playbook name
            deployment_blueprint = _ctx.blueprint.id
            if _ctx.workflow_id == 'update':
                deployment_blueprint = \
                    _get_deployment_blueprint(_ctx.deployment.id)
            file_path = \
                BP_INCLUDES_PATH.format(
                    tenant=_get_tenant_name(_ctx),
                    blueprint=deployment_blueprint,
                    relative_path=file_path)
    if os.path.exists(file_path):
        return file_path
    raise NonRecoverableError(
        'File path {0} does not exist.'.format(file_path))


def get_instance(_ctx=None):
    _ctx = _ctx or ctx
    if _ctx.type == RELATIONSHIP_INSTANCE:
        return _ctx.source.instance
    else:  # _ctx.type == NODE_INSTANCE
        return _ctx.instance


def get_node(_ctx=None, target=False):
    _ctx = _ctx or ctx
    if _ctx.type == RELATIONSHIP_INSTANCE:
        if target:
            return _ctx.target.node
        return _ctx.source.node
    else:  # _ctx.type == NODE_INSTANCE
        return _ctx.node


def handle_site_yaml(site_yaml_path, additional_playbook_files, _ctx):
    """ Create an absolute local path to the site.yaml.

    :param site_yaml_path: Relative to the blueprint.
    :param additional_playbook_files: additional playbook files relative to
      the playbook.
    :param _ctx: The Cloudify context.
    :return: The final absolute path on the system to the site.yaml.
    """

    site_yaml_real_path = os.path.abspath(
        handle_file_path(site_yaml_path, additional_playbook_files, _ctx))
    site_yaml_real_dir = os.path.dirname(site_yaml_real_path)
    site_yaml_real_name = os.path.basename(site_yaml_real_path)
    site_yaml_new_dir = os.path.join(
        get_instance(_ctx).runtime_properties[WORKSPACE], 'playbook')
    shutil.copytree(site_yaml_real_dir, site_yaml_new_dir)
    site_yaml_final_path = os.path.join(site_yaml_new_dir, site_yaml_real_name)
    return u'{0}'.format(site_yaml_final_path)


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

    hosts_abspath = os.path.join(os.path.dirname(site_yaml_abspath), HOSTS)
    if isinstance(data, dict):
        data = handle_key_data(
            data, get_instance(_ctx).runtime_properties[WORKSPACE])
        if os.path.exists(hosts_abspath):
            _ctx.logger.error(
                'Hosts data was provided but {0} already exists. '
                'Overwriting existing file.'.format(hosts_abspath))
        with open(hosts_abspath, 'w') as outfile:
            yaml.safe_dump(data, outfile, default_flow_style=False)
    elif isinstance(data, text_type):
        hosts_abspath = handle_source_from_string(data, _ctx, hosts_abspath)
    return hosts_abspath


def get_inventory_file(filepath, _ctx, new_inventory_path):
    """
    This method will get the location for inventory file.
    The file location could be locally with relative to the blueprint
    resources or it could be remotely on the remote machine
    :return:
    :param filepath: File path to do check for
    :param _ctx: The Cloudify context.
    :param new_inventory_path: New path which holds the file inventory path
    when "filepath" is a local resource
    :return: File location for inventory file
    """
    if os.path.isfile(filepath):
        # The file already exists on the system, then return the file url
        return filepath
    else:
        # Check to see if the file does not exit, then try to lookup the
        # file from the Cloudify blueprint resources
        try:
            _ctx.download_resource(filepath, new_inventory_path)
        except HttpException:
            _ctx.logger.error(
                'Error when trying to download {0}'.format(filepath))
            return None
        except RuntimeError:
            new_inventory_path = _ctx.download_resource(filepath)
        return new_inventory_path


def handle_source_from_string(filepath, _ctx, new_inventory_path):
    inventory_file = get_inventory_file(filepath, _ctx, new_inventory_path)
    if inventory_file != new_inventory_path and new_inventory_path:
        try:
            shutil.copy2(inventory_file, new_inventory_path)
        except TypeError:
            inventory_file = None
    if inventory_file:
        return inventory_file
    else:
        with open(new_inventory_path, 'w') as outfile:
            _ctx.logger.info(
                'Writing this data to temp file: {0}'.format(
                    new_inventory_path))
            outfile.write(filepath)
    return new_inventory_path


def create_ansible_cfg(ctx):
    workspace_dir = get_instance(ctx).runtime_properties.get(WORKSPACE)
    collections_location = _get_collections_location(ctx)
    ansible_cfg_file = os.path.join(workspace_dir, 'ansible.cfg')
    with open(ansible_cfg_file, 'w') as f:
        f.write("[defaults]\n")
        f.write("collections_path={}\n".format(collections_location))
        f.write("roles={}\n".format(workspace_dir))


def create_playbook_workspace(ctx=None):
    """ Create a temporary folder, so that we don't overwrite fields.
    :param ctx: The Cloudify context.
    :return:
    """
    get_instance(ctx).runtime_properties[WORKSPACE] = \
        mkdtemp(dir=get_node_instance_dir())
    create_ansible_cfg(ctx)


def delete_temp_folder(directory):
    if directory and os.path.exists(directory):
        shutil.rmtree(directory)


def delete_playbook_workspace(ctx):
    """Delete the temporary folder.

    :param ctx: The Cloudify context.
    :return:
    """

    directory = get_instance(ctx).runtime_properties.get(WORKSPACE)
    delete_temp_folder(directory)


def delete_playbook_environment(ctx):
    """Delete the temporary folder.

    :param ctx: The Cloudify context.
    :return:
    """

    directory = get_instance(ctx).runtime_properties.get(PLAYBOOK_VENV)
    delete_temp_folder(directory)


def get_source_config_from_ctx(_ctx,
                               group_name=None,
                               hostname=None,
                               host_config=None,
                               sources=None):
    """Generate a source config from CTX.

    :param _ctx: Either a NodeInstance or a RelationshipInstance ctx.
    :param group_name: User's override value, like 'webservers'.
    :param hostname: User's override value, like 'web'.
    :param host_config: User's override value. Like:
       {
           'ansible_host': '127.0.0.1',
           'ansible_user': 'ubuntu',
       }
    :param sources: User's sources override value.
    :return:
    """

    sources = sources or {}
    if _ctx.type == NODE_INSTANCE and \
            'cloudify.nodes.Compute' not in _ctx.node.type_hierarchy and \
            _ctx.instance.runtime_properties.get(SOURCES):
        if isinstance(_ctx.instance.runtime_properties[SOURCES], text_type):
            if os.path.exists(_ctx.instance.runtime_properties[SOURCES]):
                return _ctx.instance.runtime_properties[SOURCES]
            else:
                return _ctx.download_resource(
                    _ctx.instance.runtime_properties[SOURCES])
        return AnsibleSource(_ctx.instance.runtime_properties[SOURCES]).config
    elif _ctx.type == RELATIONSHIP_INSTANCE:
        host_config = host_config or \
            get_host_config_from_compute_node(_ctx.target)
        group_name, hostname = \
            get_group_name_and_hostname(
                _ctx.target, group_name, hostname)
        additional_node_groups = get_additional_node_groups(
            _ctx.target.node.name, _ctx.deployment.id)
    else:
        host_config = host_config or \
            get_host_config_from_compute_node(_ctx)
        group_name, hostname = \
            get_group_name_and_hostname(
                _ctx, group_name, hostname)
        additional_node_groups = get_additional_node_groups(
            get_node(_ctx).name, _ctx.deployment.id)
    if '-o StrictHostKeyChecking=no' not in \
            host_config.get('ansible_ssh_common_args', ''):
        _ctx.logger.warn(
            'This value {0} is not included in Ansible Configuration. '
            'This is required for automating host key approval.'.format(
                {'ansible_ssh_common_args': '-o StrictHostKeyChecking=no'}))
    hosts = {
        hostname: host_config
    }
    sources[group_name] = {
        HOSTS: hosts
    }
    for additional_group in additional_node_groups:
        sources[additional_group] = {HOSTS: {hostname: None}}
    return AnsibleSource(sources).config


def update_sources_from_target(new_sources_dict, _ctx):
    # get source sources
    current_sources_dict = _ctx.source.instance.runtime_properties.get(
        SOURCES, {})
    current_sources = AnsibleSource(current_sources_dict)
    # get target sources
    new_sources = AnsibleSource(new_sources_dict)
    # merge sources
    current_sources.merge_source(new_sources)
    # save sources to source node
    _ctx.source.instance.runtime_properties[SOURCES] = current_sources.config
    return current_sources.config


def cleanup_sources_from_target(new_sources_dict, _ctx):
    # get source sources
    current_sources_dict = _ctx.source.instance.runtime_properties.get(
        SOURCES, {})
    current_sources = AnsibleSource(current_sources_dict)
    # get target sources
    new_sources = AnsibleSource(new_sources_dict)
    # merge sources
    current_sources.remove_source(new_sources)
    # save sources to source node
    _ctx.source.instance.runtime_properties[SOURCES] = current_sources.config
    return current_sources.config


def get_remerged_config_sources(_ctx, kwargs):
    if _ctx.type == RELATIONSHIP_INSTANCE:
        group_name = kwargs.get('group_name')
        hostname = kwargs.get('hostname')
        host_config = kwargs.get('host_config', {})
        # get target sources
        new_sources_dict = get_source_config_from_ctx(
            _ctx, group_name, hostname, host_config)
        # merged sources
        merged_sources = update_sources_from_target(new_sources_dict, _ctx)
        return AnsibleSource(merged_sources).config
    else:
        return get_source_config_from_ctx(_ctx)


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
        'ansible_ssh_pass': _ctx.node.properties.get(
            'agent_config', {}).get('password'),
        'ansible_ssh_private_key_file':
            _ctx.node.properties.get('agent_config', {}).get('key'),
        'ansible_ssh_common_args': '-o StrictHostKeyChecking=no',
        'ansible_become': _ctx.node.properties.get('ansible_become', True)
    }


def handle_result(result, _ctx, ignore_failures=False, ignore_dark=False):
    _ctx.logger.debug('result: {0}'.format(result))
    get_instance(_ctx).runtime_properties['result'] = result
    failures = result.get('failures')
    dark = result.get('dark')
    if failures and not ignore_failures:
        raise NonRecoverableError(
            'These Ansible nodes failed: {0}'.format(failures))
    elif dark and not ignore_dark:
        raise OperationRetry(
            'These Ansible nodes were dark: {0}'.format(dark))


def assign_environ(_vars):
    for key, value in _vars.items():
        os.environ[key] = value


def unassign_environ(_vars):
    for key in _vars.keys():
        del os.environ[key]


def get_additional_node_groups(node_name, deployment_id):
    """This enables users to reuse hosts in multiple groups."""
    groups = []
    try:
        client = get_rest_client()
    except KeyError:
        return groups
    deployment = client.deployments.get(deployment_id)
    for group_name, group in deployment.get('groups', {}).items():
        if node_name in group.get('members', []) and group_name:
            groups.append(group_name)
    return groups


def cleanup(ctx):
    """
    Unset all runtime properties from node instance when delete operation
    task if finished
    :param ctx: Cloudify node instance which is could be an instance of
    RelationshipSubjectContext or CloudifyContext
    """
    instance = get_instance(ctx)
    for key, _ in list(instance.runtime_properties.items()):
        del instance.runtime_properties[key]


def set_playbook_config_as_runtime_properties(_ctx, config):
    """
    Set all playbook node instance configuration as runtime properties
    :param _ctx: Cloudify node instance which is instance of CloudifyContext
    :param config: Playbook node configurations
    """
    def _get_secure_values(data, sensitive_keys, parent_hide=False):
        """
        ::param data : dict to check againt sensitive_keys
        ::param sensitive_keys : a list of keys we want to hide the values for
        ::param parent_hide : boolean flag to pass if the parent key is
                                in sensitive_keys
        """
        for key in data:
            # check if key or its parent {dict value} in sensitive_keys
            hide = parent_hide or (key in sensitive_keys)
            value = data[key]
            # handle dict value in case sensitive_keys was inside another key
            if isinstance(value, dict):
                # call _get_secure_value function recursively
                # to handle the dict value
                inner_dict = _get_secure_values(value, sensitive_keys, hide)
                data[key] = inner_dict
            else:
                data[key] = '*' * len(value) if hide else value
        return data

    if config and isinstance(config, dict):
        config = _get_secure_values(config, config.get("sensitive_keys", {}))
        for key, value in config.items():
            _ctx.instance.runtime_properties[key] = value


def make_virtualenv(path):
    """
        Make a venv for installing ansible module inside.
    """
    ctx.logger.debug("Creating virtualenv at: {path}".format(path=path))
    runner.run([
        sys.executable, '-m', 'virtualenv', path
    ])


def is_local_venv():
    return get_instance(ctx).runtime_properties.get(LOCAL_VENV)


def set_installed_packages(venv):
    installed_packages = runner.run([get_executable_path('pip', venv=venv),
                                     'freeze']).std_out
    ctx.instance.runtime_properties[INSTALLED_PACKAGES] = installed_packages


def install_packages_to_venv(venv, packages_list):
    # Force reinstall in playbook venv in order to make sure
    # they being installed on specified environment .
    if packages_list:
        ctx.logger.debug("venv = {path}".format(path=venv))
        command = [get_executable_path('pip', venv=venv), 'install',
                   '--force-reinstall', '--retries=2',
                   '--timeout=15'] + packages_list
        ctx.logger.debug("cmd:{command}".format(command=command))
        ctx.logger.info("Installing {packages} on playbook`s venv.".format(
            packages=packages_list))
        try:
            runner.run(command=command,
                       cwd=venv,
                       execution_env={'LANG': 'en_US.UTF-8', 'PYTHONPATH': ''})
        except CommandExecutionException as e:
            raise NonRecoverableError("Can't install extra_package on"
                                      " playbook`s venv. Error message: "
                                      "{err}".format(err=e))
    set_installed_packages(venv)


def install_collections_to_venv(venv, collections_list, collections_dir):
    # Force reinstall in playbook venv in order to make sure
    # they being installed on specified environment .
    if collections_list:
        ctx.logger.debug("venv = {path}".format(path=venv))
        command = [get_executable_path('ansible-galaxy', venv=venv),
                   'collection',
                   'install',
                   '--force',
                   '-p',
                   collections_dir] + collections_list
        ctx.logger.debug("cmd:{command}".format(command=command))
        ctx.logger.info("Installing {packages} on playbook`s venv.".format(
            packages=collections_list))
        get_command = [get_executable_path('ansible-galaxy', venv=venv),
                       'collection',
                       'list',
                       '-p',
                       collections_dir]
        try:
            runner.run(command=command,
                       cwd=venv,
                       execution_env={'LANG': 'en_US.UTF-8', 'PYTHONPATH': ''})
            installed_collections = \
                runner.run(command=get_command,
                           cwd=venv,
                           execution_env={
                               'LANG': 'en_US.UTF-8',
                               'PYTHONPATH': ''}
                           )
            get_instance(ctx).runtime_properties[INSTALLED_COLLECTIONS] = \
                installed_collections.std_out
        except CommandExecutionException as e:
            raise NonRecoverableError("Can't install galaxy_collections on"
                                      " playbook`s venv. Error message: "
                                      "{err}".format(err=e))


def install_roles_to_venv(venv, roles_list, roles_dir):
    # Force reinstall in playbook venv in order to make sure
    # they being installed on specified environment .
    if roles_list:
        ctx.logger.debug("venv = {path}".format(path=venv))
        command = [get_executable_path('ansible-galaxy', venv=venv),
                   'install',
                   '--force',
                   '-p',
                   roles_dir] + roles_list
        ctx.logger.debug("cmd:{command}".format(command=command))
        ctx.logger.info("Installing {packages} in location {location}.".format(
            packages=roles_list,
            location=roles_dir))
        get_command = [get_executable_path('ansible-galaxy', venv=venv),
                       'list',
                       '-p',
                       roles_dir]
        try:
            runner.run(command=command,
                       cwd=venv,
                       execution_env={'LANG': 'en_US.UTF-8', 'PYTHONPATH': ''})
            installed_roles = \
                runner.run(command=get_command,
                           cwd=venv,
                           execution_env={
                               'LANG': 'en_US.UTF-8',
                               'PYTHONPATH': ''}
                           )
            get_instance(ctx).runtime_properties[INSTALLED_ROLES] = \
                installed_roles.std_out
        except CommandExecutionException as e:
            raise NonRecoverableError("Can't install roles on"
                                      " playbook`s venv. Error message: "
                                      "{err}".format(err=e))


def get_executable_path(executable, venv):
    """
    :param executable: the name of the executable
    :param venv: the venv to look for the executable in.
    """
    return '{0}/bin/{1}'.format(venv, executable) if venv else executable


def install_new_pyenv_condition(_ctx):
    if get_instance(_ctx).runtime_properties.get(PLAYBOOK_VENV):
        _ctx.logger.info(
            "Using installed pyenv: {}"
            .format(
                get_instance(_ctx).runtime_properties.get(PLAYBOOK_VENV)
            )
        )
        return False
    if _ctx.node.properties.get('ansible_external_pyenv'):
        get_instance(_ctx).runtime_properties[PLAYBOOK_VENV] = \
            _ctx.node.properties.get('ansible_external_pyenv')
        _ctx.logger.info(
            "Using installed pyenv: {}"
            .format(
                _ctx.node.properties.get('ansible_external_pyenv')
            )
        )
        return False
    if _ctx.node.properties.get('ansible_external_executable_path'):
        _ctx.logger.info(
            "Using installed executable path: {}"
            .format(
                _ctx.node.properties.get('ansible_external_executable_path')
            )
        )
        return False
    return True


def install_galaxy_collections(_ctx,
                               collections_to_install=None):
    """
        Handle creation of virtual environments for running playbooks.
        The virtual environments will be created at the deployment directory.
       :param _ctx: cloudify context.
       :param collections_to_install: list of galaxy collections to install
        inside venv.
       """

    if collections_to_install:
        if is_connected_to_internet():
            venv_path = get_instance(ctx).runtime_properties.get(PLAYBOOK_VENV)
            collections_location = _get_collections_location(_ctx)
            _ctx.logger.info("Installing collections {} to path {}".format(
                str(collections_to_install),
                collections_location))
            install_collections_to_venv(venv_path,
                                        collections_to_install,
                                        collections_location)
        else:
            raise NonRecoverableError('No internet connection.'
                                      'Do not use galaxy_collections when'
                                      ' working on the plugin virtualenv.')


def install_roles(_ctx,
                  roles_to_install=None):
    """
        Handle creation of virtual environments for running playbooks.
        The virtual environments will be created at the deployment directory.
       :param _ctx: cloudify context.
       :param roles_to_install: list of roles to install
       """

    if roles_to_install:
        if is_connected_to_internet():
            venv_path =\
                get_instance(ctx).runtime_properties.get(PLAYBOOK_VENV)
            roles_location = _get_roles_location(_ctx)
            _ctx.logger.info("Installing roles {} to path {}".format(
                str(roles_to_install),
                roles_location))
            install_roles_to_venv(venv_path,
                                  roles_to_install,
                                  roles_location)
        else:
            raise NonRecoverableError('No internet connection.'
                                      'Do not use roles when'
                                      ' working on the plugin virtualenv.')


def install_extra_packages(_ctx,
                           packages_to_install=None):
    """
        Handle creation of virtual environments for running playbooks.
        The virtual environments will be created at the deployment directory.
       :param _ctx: cloudify context.
       :param packages_to_install: list of python packages to install
        inside venv.
       """

    if packages_to_install:
        if is_connected_to_internet():
            if is_local_venv():
                venv_path = \
                    get_instance(_ctx).runtime_properties.get(PLAYBOOK_VENV)
                _ctx.logger.info(
                    "Installing extra_packages {} to path {}".format(
                        str(packages_to_install),
                        venv_path)
                )
                install_packages_to_venv(venv_path, packages_to_install)
        else:
            raise NonRecoverableError('No internet connection.'
                                      'Do not use extra_packages when'
                                      ' working on the plugin virtualenv.')


def create_playbook_venv(_ctx):
    """
        Handle creation of virtual environments for running playbooks.
        The virtual environments will be created at the deployment directory.
       :param _ctx: cloudify context.
       """

    if is_connected_to_internet():
        if install_new_pyenv_condition(_ctx):
            _ctx.logger.info("Installing new python venv")
            deployment_dir = get_deployment_dir(_ctx.deployment.id)
            venv_path = mkdtemp(dir=deployment_dir)
            make_virtualenv(path=venv_path)
            ansible_to_install = [ANSIBLE_TO_INSTALL]
            if _ctx.node.properties.get('installation_source'):
                ansible_to_install = [
                    _ctx.node.properties['installation_source']
                ]
            install_packages_to_venv(venv_path, ansible_to_install)
            get_instance(_ctx).runtime_properties[PLAYBOOK_VENV] = venv_path
            get_instance(_ctx).runtime_properties[LOCAL_VENV] = True

    else:
        get_instance(_ctx).runtime_properties[PLAYBOOK_VENV] = ''


def is_connected_to_internet():
    try:
        urlopen('http://google.com', timeout=5)
        ctx.logger.debug("Connected to internet.")
        return True
    except URLError:
        ctx.logger.debug("No Internet connection.")
        return False


def process_execution(script_func, script_path, ctx, process=None):
    """Entirely lifted from the script runner, the only difference is
    we return the return value of the script_func, instead of the return
    code stored in the ctx.

    :param script_func:
    :param script_path:
    :param ctx:
    :param process:
    :return:
    """
    ctx.is_script_exception_defined = ScriptException is not None

    def abort_operation(message=None):
        if ctx._return_value is not None:
            ctx._return_value = ILLEGAL_CTX_OPERATION_ERROR
            raise ctx._return_value
        if ctx.is_script_exception_defined:
            ctx._return_value = ScriptException(message)
        else:
            ctx._return_value = UNSUPPORTED_SCRIPT_FEATURE_ERROR
            raise ctx._return_value
        return ctx._return_value

    def retry_operation(message=None, retry_after=None):
        if ctx._return_value is not None:
            ctx._return_value = ILLEGAL_CTX_OPERATION_ERROR
            raise ctx._return_value
        if ctx.is_script_exception_defined:
            ctx._return_value = ScriptException(message, retry=True)
            ctx.operation.retry(message=message, retry_after=retry_after)
        else:
            ctx._return_value = UNSUPPORTED_SCRIPT_FEATURE_ERROR
            raise ctx._return_value
        return ctx._return_value

    ctx.abort_operation = abort_operation
    ctx.retry_operation = retry_operation

    def returns(value):
        if ctx._return_value is not None:
            ctx._return_value = ILLEGAL_CTX_OPERATION_ERROR
            raise ctx._return_value
        ctx._return_value = value
    ctx.returns = returns

    ctx._return_value = None

    actual_result = script_func(script_path, ctx, process)
    script_result = ctx._return_value
    if ctx.is_script_exception_defined and isinstance(
            script_result, ScriptException):
        if script_result.retry:
            return script_result
        else:
            raise NonRecoverableError(str(script_result))
    else:
        return actual_result


def get_plays(string, node_name):
    """When play output is returned in JSON, we can parse it and
    retrieve only the play dictionary. This is a little messy, and it's
    not actually used in the plugin. I want to leave it hear for now,
    for a future time when someone will ask for how to get plays from the
    JSON command output. It might never be used, but it's good for us
    to have just in case.

    :param string:
    :param node_name:
    :return:
    """
    string_without_whitespace = '\n'.join(
        string).replace("\n", "").replace("\t", "").replace(" ", "")
    surrounding_elements = ',"plays":(.*),"stats":{"' + node_name
    selected = re.search(surrounding_elements, string_without_whitespace)
    try:
        return json.loads(selected.group(1))
    except (AttributeError, IndexError):
        ctx.logger.info('Unable to parse result. '
                        'Not storing result in runtime properties.')
        return string_without_whitespace


def get_facts(string):
    """Facts are collected in the ansible check command.
    This output is returned in string, and then we need to split the string,
    and then parse the JSON embedded in the string.
    There is currently not a better way to do this. A thousand curses on
    Ansible for dumping mixed format output.

    :param string:
    :return:
    """
    # ctx.logger.info('TRYING THIS')
    # ctx.logger.info(string)
    new_string = []
    for line in string.split('\n'):
        if line.startswith('META'):
            continue
        line = line.replace('META: ran handlers', '')
        new_string.append(line)
    separater = '=>(.*)'
    string_without_whitespace = '\n'.join(
        new_string).replace("\n", "").replace("\t", "")
    selected = re.search(separater, string_without_whitespace)
    try:
        return json.loads(selected.group(1))['ansible_facts']
    except (AttributeError, IndexError, KeyError) as e:
        ctx.logger.error(
            'Unable to parse result. '
            'Not storing result in runtime properties. Error: {}'.format(e))
    return selected


def get_tasks_by_host(plays):
    """Find all the task names associated with a host. Currently not used."""
    task_names = []
    for play in plays:
        for task in play['tasks']:
            task_names.append(task['task']['name'])
    return task_names


def process_block_tags(block, tasks, tags):
    """ Get tags from blocks in a playbook. Uses Ansible as a programming
    library. Copied from Ansible.

    :param block:
    :param tasks:
    :param tags:
    :return:
    """
    for task in block.block:
        if isinstance(task, type(block)):
            process_block_tags(task, tasks)
        else:
            if task.action == 'meta':
                continue
            tasks.append(task.name.replace(' ', ''))
            for tag in task.tags:
                if tag not in tags:
                    tags.append(tag)


def get_tags_from_playbook(playbook):
    """ Get a list of tag names

    :param playbook: ansible.playbook.Playbook
    :return: list
    """
    tasks = []
    tags = []
    for play in playbook.get_plays():
        for block in play.compile():
            process_block_tags(block, tasks, tags)
    return tasks, tags


def get_playbook_from_path(playbook_path):
    """ Create ansible.playbook.Playbook object.

    :param playbook_path: string
    :return:
    """
    loader = DataLoader()
    variable_manager = VariableManager(loader=loader)
    return Playbook.load(
        file_name=playbook_path,
        variable_manager=variable_manager,
        loader=loader)


def get_available_steps(playbook_path):
    return get_tags_from_playbook(get_playbook_from_path(playbook_path))


def get_our_tags(all_tags, op_number, max_ops):
    """Given a list of tags, calculate the number that we need to run
    in successive retries in order to finish them all in the
    maximum number of retries.

    :param all_tags:
    :param op_number:
    :param max_ops:
    :return:
    """
    if not all_tags:
        return [], []
    for num, tag in enumerate(all_tags):
        if tag == '':
            all_tags.remove(num)
    remaining_operations = max_ops - op_number
    our_tags = deepcopy(all_tags)
    remaining_tags = len(our_tags)
    if remaining_tags > remaining_operations:
        our_tags = our_tags[0:round(remaining_tags // remaining_operations)]
    else:
        our_tags = [our_tags[0]]
    for tag in our_tags:
        all_tags.remove(tag)
    return our_tags, all_tags


def get_playbook_args_tags(_node, _instance, playbook_path):
    """ Check which tags are completed of all available tags.

    :param _node:
    :param _instance:
    :param playbook_path:
    :return:
    """

    if AVAILABLE_TAGS not in _instance.runtime_properties:
        tags = _node.properties.get('tags', [])
        if tags:
            _instance.runtime_properties[AVAILABLE_TAGS] = tags
        elif _node.properties.get('auto_tags', False):
            _, tags = get_available_steps(playbook_path)
            _instance.runtime_properties[AVAILABLE_TAGS] = tags
        else:
            _instance.runtime_properties[AVAILABLE_TAGS] = tags
    else:
        tags = _instance.runtime_properties[AVAILABLE_TAGS]

    if COMPLETED_TAGS in _instance.runtime_properties:
        for tag in _instance.runtime_properties[COMPLETED_TAGS]:
            if tag in tags:
                tags.remove(tag)

    return get_our_tags(
        tags,
        ctx.operation.retry_number,
        ctx.operation.max_retries)


def raise_if_retry_is_not_allowed(actual_retry_number,
                                  allowed_attempts_number):
    """
    Raise NonRecoverableError if the playbook failed more than the number of
    attempts that the user allowed.
    """
    # actual_retry_number starts from 0.
    actual_attempts = actual_retry_number + 1
    if actual_attempts >= allowed_attempts_number:
        raise NonRecoverableError(
            'Number of attempts: {actual_attempts} is greater or equal'
            ' than retry_number allowed:{allowed_attempts}'.format(
                actual_attempts=actual_attempts,
                allowed_attempts=allowed_attempts_number))
