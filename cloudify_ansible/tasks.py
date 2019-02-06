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


def _execute_playbook(playbook_args):
    try:
        pb = AnsiblePlaybookFromFile(**playbook_args)
    except CloudifyAnsibleSDKError:
        raise NonRecoverableError(CloudifyAnsibleSDKError)
    return pb.execute()


@operation
def execute(site_yaml_path,
            fail_on_unreachable=False,
            fail_on_skipped=None,
            log_output=True,
            _ctx=ctx,
            **kwargs):

    kwargs.update({'site_yaml_path': site_yaml_path})

    if log_output:
        _ctx.logger.info(
            'Executing playbook with these args: {0}'.format(kwargs))

    output = _execute_playbook(kwargs)

    if log_output:
        _ctx.logger.info('Playbook run output: {0}'.format(output))

    errors = []

    if fail_on_unreachable and \
            (output.get('dark') or output.get('unreachable')):
        errors.append(output.get('dark') or output.get('unreachable'))
    if fail_on_skipped and output.get('skipped'):
        errors.append(output.get('skipped'))
    if errors:
        raise NonRecoverableError(
            'These errors were encountered {errors}'.format(errors=errors))
