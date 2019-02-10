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
import yaml

from cloudify.exceptions import NonRecoverableError

BP_INCLUDES_PATH = '/opt/manager/resources/blueprints/' \
                   '{tenant}/{blueprint}/{relative_path}'


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
        _ctx.instance.runtime_properties['workspace'], 'playbook')
    shutil.copytree(site_yaml_real_dir, site_yaml_new_dir)
    site_yaml_final_path = os.path.join(site_yaml_new_dir, site_yaml_real_name)
    # TODO: Before merge change this to debug.
    with open(site_yaml_final_path, 'r') as infile:
        _ctx.logger.info('Contents site.yaml:\n {0}'.format(infile.read()))
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
        if os.path.exists(hosts_abspath):
            _ctx.logger.error(
                'Hosts data was provided but {0} already exists. '
                'Overwriting existing file.'.format(hosts_abspath))
        with open(hosts_abspath, 'w') as outfile:
            _ctx.logger.info(
                'Writing this data to temp file: {0}'.format(data))
            yaml.dump(data, outfile, default_flow_style=False)
    # TODO: Before merge change this to debug.
    with open(hosts_abspath, 'r') as infile:
        _ctx.logger.info('Contents hosts:\n {0}'.format(infile.read()))
    return hosts_abspath


def create_playbook_workspace(ctx):
    """ Create a temporary folder, so that we don't overwrite fields.

    :param ctx: The Cloudify context.
    :return:
    """

    ctx.instance.runtime_properties['workspace'] = mkdtemp()


def delete_playbook_workspace(ctx):
    """Delete the temporary folder.

    :param ctx: The Cloudify context.
    :return:
    """

    directory = ctx.instance.runtime_properties.get('workspace')
    if directory and os.path.exists(directory):
        shutil.rmtree(directory)
