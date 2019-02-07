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
    AnsiblePlaybookFromFile, CloudifyAnsibleSDKError)

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError


@operation
def run(site_yaml_path,
        sources=None,
        ctx=ctx,
        **kwargs):

    playbook_args = {
        'site_yaml_path': site_yaml_path,
        'sources': sources,
    }

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
