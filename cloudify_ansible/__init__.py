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

from cloudify import ctx as ctx_from_import

from cloudify_common_sdk.resource_downloader import untar_archive
from cloudify_common_sdk.resource_downloader import unzip_archive
from cloudify_common_sdk.resource_downloader import get_shared_resource
from cloudify_common_sdk.resource_downloader import TAR_FILE_EXTENSTIONS

from cloudify.exceptions import NonRecoverableError

from cloudify_ansible_sdk import DIRECT_PARAMS
from cloudify_ansible import constants
from cloudify_ansible.utils import (
    get_node,
    get_instance,
    install_roles,
    setup_modules,
    handle_sources,
    setup_kerberos,
    handle_site_yaml,
    create_playbook_venv,
    install_extra_packages,
    create_playbook_workspace,
    install_galaxy_collections,
    get_source_config_from_ctx,
    get_remerged_config_sources,
)


def ansible_relationship_source(func):
    def wrapper(group_name=None,
                hostname=None,
                host_config=None,
                ctx=ctx_from_import):
        source_dict = get_source_config_from_ctx(
            ctx, group_name, hostname, host_config)
        func(source_dict, ctx)

    return wrapper


def set_ansible_env_vars(ansible_env_vars=None):
    ansible_env_vars = ansible_env_vars or {}
    if constants.OPTION_HOST_CHECKING not in ansible_env_vars:
        ansible_env_vars[constants.OPTION_HOST_CHECKING] = "False"
    if constants.OPTION_STDOUT_FORMAT not in ansible_env_vars:
        ansible_env_vars[constants.OPTION_STDOUT_FORMAT] = "json"
    if constants.OPTION_TASK_FAILED_ATTRIBUTE not in ansible_env_vars:
        ansible_env_vars[constants.OPTION_TASK_FAILED_ATTRIBUTE] = "False"
    return ansible_env_vars


def ansible_playbook_node(func):
    def wrapper(playbook_path=None,
                sources=None,
                ctx=ctx_from_import,
                ansible_env_vars=None,
                debug_level=2,
                additional_args=None,
                additional_playbook_files=None,
                site_yaml_path=None,
                remerge_sources=False,
                playbook_source_path=None,
                extra_packages=None,
                galaxy_collections=None,
                roles=None,
                module_path=None,
                **kwargs):
        """Prepare the arguments to send to AnsiblePlaybookFromFile.

        :param site_yaml_path:
            The absolute or relative (blueprint) path to the site.yaml.
        :param sources: Either a path (with the site.yaml).
            Or a YAML dictionary (from the blueprint itself).
        :param ctx: The cloudify context.
        :param ansible_env_vars:
          A dictionary of environment variables to set.
        :param debug_level: Debug level
        :param additional_args: Additional args that you want to use, for
          example, '-c local'.
        :param site_yaml_path: A path to your `site.yaml` or `main.yaml` in
          your Ansible Playbook.
        :param save_playbook: don't remove playbook after action
        :param remerge_sources: update sources on target node
        :param extra_packages: list of packages to install to ansible playbook
         controller env.
        :param galaxy_collections: list of ansible galaxy collections to
         install to controller env.
        :param roles: list of roles to install to working directory
        :param start_at_task: The name of the task to start at.
        :param kwargs:
        :return:
        """
        playbook_path = playbook_path or site_yaml_path
        additional_playbook_files = additional_playbook_files or []
        ansible_env_vars = set_ansible_env_vars(ansible_env_vars)
        _instance = get_instance(ctx)
        if not sources:
            if remerge_sources:
                # add sources from source node to target node
                sources = get_remerged_config_sources(ctx, kwargs)
            else:
                sources = get_source_config_from_ctx(ctx)

        # store sources in node runtime_properties
        _instance.runtime_properties['sources'] = sources

        try:
            handle_venv(ctx,
                        extra_packages,
                        galaxy_collections,
                        roles,
                        module_path)
            # check if source path is provided [full path/URL]
            if playbook_source_path:
                # here we will combine playbook_source_path with playbook_path
                playbook_tmp_path = get_shared_resource(playbook_source_path)
                if playbook_tmp_path == playbook_source_path:
                    # didn't download anything so check the provided path
                    # if file and absolute path
                    if os.path.isfile(playbook_tmp_path) and \
                            os.path.isabs(playbook_tmp_path):
                        # check file type if archived
                        file_name = playbook_tmp_path.rsplit('/', 1)[1]
                        file_type = file_name.rsplit('.', 1)[1]
                        if file_type == 'zip':
                            playbook_tmp_path = \
                                unzip_archive(playbook_tmp_path)
                        elif file_type in TAR_FILE_EXTENSTIONS:
                            playbook_tmp_path = \
                                untar_archive(playbook_tmp_path)
                playbook_path = "{0}/{1}".format(playbook_tmp_path,
                                                 playbook_path)
            else:
                # here will handle the bundled ansible files
                playbook_path = handle_site_yaml(
                    playbook_path, additional_playbook_files, ctx)

            playbook_args = {
                'playbook_path': playbook_path,
                'module_path': _instance.runtime_properties.get('module_path'),
                'sources': handle_sources(sources, playbook_path, ctx),
                'verbosity': debug_level,
                'additional_args': additional_args or '',
                'logger': ctx.logger
            }

            # copy additional params from kwargs
            for field in DIRECT_PARAMS:
                if kwargs.get(field):
                    playbook_args[field] = kwargs[field]

            playbook_args.update(**kwargs)
            try:
                func(playbook_args, ansible_env_vars, ctx)
            except NonRecoverableError as e:
                node = get_node(ctx)
                if 'poststart' in ctx.operation.name and \
                        not node.properties.get('sources'):
                    ctx.logger.error(
                        'No sources property was provided,'
                        ' so skipping storing facts.')
                    return
                raise e
        except NonRecoverableError as e:
            raise e

    return wrapper


def prepare_ansible_node(func):
    def wrapper(ctx=ctx_from_import,
                extra_packages=None,
                galaxy_collections=None,
                roles=None,
                module_path=None,
                **kwargs):
        handle_venv(
            ctx,
            extra_packages,
            galaxy_collections,
            roles,
            module_path)
        func(ctx, **kwargs)
    return wrapper


def handle_venv(ctx=None,
                extra_packages=None,
                galaxy_collections=None,
                roles=None,
                module_path=None):
    ctx = ctx or ctx_from_import
    extra_packages = extra_packages or get_node(ctx).properties.get(
        'extra_packages') or []
    galaxy_collections = \
        galaxy_collections or get_node(ctx).properties.get(
            'galaxy_collections') or []
    create_playbook_venv(ctx)
    create_playbook_workspace(ctx)
    setup_modules(ctx, module_path)
    setup_kerberos(ctx)
    install_extra_packages(ctx, extra_packages)
    install_galaxy_collections(ctx, galaxy_collections)
    install_roles(ctx, roles)
