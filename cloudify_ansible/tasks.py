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

from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from cloudify_ansible_sdk import (
    AnsiblePlaybookFromFile,
    CloudifyAnsibleSDKError
)

from cloudify_ansible import playbook_and_sources


@operation
@playbook_and_sources
def run(playbook_args, _ctx, **_):
    _ctx.logger.info('playbook_args: {0}'.format(playbook_args))
    try:
        result = AnsiblePlaybookFromFile(**playbook_args).execute()
        _ctx.logger.debug('result: {0}'.format(result.__dict__))
        _ctx.instance.runtime_properties['result'] = result.__dict__
    except CloudifyAnsibleSDKError:
        raise NonRecoverableError(CloudifyAnsibleSDKError)
