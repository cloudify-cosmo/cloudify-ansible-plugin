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
from cloudify.exceptions import OperationRetry

from cloudify_common_sdk.resource_downloader import get_shared_resource
from cloudify_common_sdk.resource_downloader import unzip_archive
from cloudify_common_sdk.resource_downloader import untar_archive
from cloudify_common_sdk.resource_downloader import TAR_FILE_EXTENSTIONS

from cloudify_ansible_sdk import DIRECT_PARAMS
from cloudify_ansible import constants
from cloudify_ansible.utils import (
    get_node,
    get_facts,
    get_plays,
    get_our_tags,
    get_instance,
    handle_sources,
    handle_site_yaml,
    get_tasks_by_host,
    get_available_steps,
    create_playbook_venv,
    create_playbook_workspace,
    delete_playbook_workspace,
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
                save_playbook=False,
                remerge_sources=False,
                playbook_source_path=None,
                extra_packages=None,
                start_at_task=None,
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
        :param start_at_task: The name of the task to start at.
        :param kwargs:
        :return:
        """
        playbook_path = playbook_path or site_yaml_path
        additional_playbook_files = additional_playbook_files or []
        ansible_env_vars = set_ansible_env_vars(ansible_env_vars)
        if not sources:
            if remerge_sources:
                # add sources from source node to target node
                sources = get_remerged_config_sources(ctx, kwargs)
            else:
                sources = get_source_config_from_ctx(ctx)

        # store sources in node runtime_properties
        _instance = get_instance(ctx)
        _instance.runtime_properties['sources'] = sources
        _instance.update()

        try:
            extra_packages = extra_packages or get_node(ctx).properties.get(
                'extra_packages') or []
            create_playbook_venv(ctx,
                                 packages_to_install=extra_packages)
            create_playbook_workspace(ctx)
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
            func(playbook_args, ansible_env_vars, ctx)

        finally:
            if not save_playbook:
                delete_playbook_workspace(ctx)
    return wrapper
