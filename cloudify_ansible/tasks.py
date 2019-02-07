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

from cloudify_ansible_sdk import (
    AnsiblePlaybookFromFile,
    CloudifyAnsibleSDKError
)

from cloudify import ctx as ctx_from_import
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError


def handle_file_path(file_path, _ctx):
    """Get the path to a file.

    I do this for two reasons:
      1. The Download Resource only downloads an individual file.
      Ansible Playbooks are often many files.
      2. I have not figured out how to pass a file as an in
      memory object to the PlaybookExecutor class.

    :param file_path: The `site_yaml_path` from `run`.
    :param _ctx: The `ctx` from `run`.
    :return: The absolute path on the manager to the file.
    """

    local_profile = getattr(_ctx, '_local', False)
    if not local_profile:
        # After upload the blueprint is uncompressed and
        # all files are stored in:
        # /opt/manager/resources/blueprints/tenant_id/blueprint_id
        file_path = \
            '/opt/manager/resources/blueprints/' \
            '{tenant}/{blueprint}/{relative_path}'.format(
                tenant=_ctx.tenant_name,
                blueprint=_ctx.blueprint.id,
                relative_path=file_path)
    return file_path


@operation
def run(site_yaml_path,
        sources=None,
        ctx=ctx_from_import,
        **kwargs):

    """Run an Ansible playbook as an operation.

    In the following node template example,
    a user provides path to a site.yaml and sources hosts file.

    ```
      ansible_playbook:
        type: cloudify.nodes.Root
        interfaces:
          cloudify.interfaces.lifecycle:
            create:
              implementation: ansible.cloudify_ansible.tasks.run
              inputs:
                site_yaml_path: { get_input: site_yaml_relative_path }
                sources: { get_input: hosts_relative_path }
    ```

    :param site_yaml_path: A path for site.yaml file,
        that is relative to the blueprint file.
        This value is transformed on Cloudify Manager.
    :param sources:  A path for hosts file,
        that is relative to the blueprint file.
        This value is transformed on Cloudify Manager.
    :param ctx: This cloudify CTX is
        received from the operation decorator.
        Tests and other Python modules can override it for testing.
    :param kwargs: keyword args for the
        Cloudify AnsiblePlaybookFromFile module.
    :return: None
    """

    # Get the actual file path.
    site_yaml_path = handle_file_path(site_yaml_path, ctx)
    sources = handle_file_path(sources, ctx)

    # Prepare kwargs for the AnsiblePlaybookFromFile class.
    playbook_args = {
        'site_yaml_path': site_yaml_path,
        'sources': sources,
    }

    # Set the verbosity to 0 by default.
    if 'verbosity' not in kwargs:
        kwargs['verbosity'] = 0

    playbook_args.update(**kwargs)

    ctx.logger.info('playbook_args: {0}'.format(playbook_args))

    try:
        playbook = AnsiblePlaybookFromFile(**playbook_args)
    except CloudifyAnsibleSDKError:
        raise NonRecoverableError(CloudifyAnsibleSDKError)

    result = playbook.execute()

    ctx.instance.runtime_properties['result'] = result.__dict__
    ctx.logger.debug(
        'Playbook run results: {0}'.format(
            ctx.instance.runtime_properties['result']))
