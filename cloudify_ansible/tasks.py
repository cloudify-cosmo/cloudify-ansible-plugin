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
from cloudify.exceptions import (
    NonRecoverableError,
    OperationRetry
)

from script_runner.tasks import (
    execute,
    process_execution,
    ProcessException
)

from cloudify_ansible_sdk import (
    AnsiblePlaybookFromFile,
    CloudifyAnsibleSDKError
)
from cloudify_ansible import (
    ansible_playbook_node,
    ansible_relationship_source,
    utils
)

UNREACHABLE_CODES = [None, 2, 4]
SUCCESS_CODES = [0]


@operation(resumable=True)
def cleanup(ctx, **_):
    utils.cleanup(ctx)


@operation(resumable=True)
def set_playbook_config(ctx, **kwargs):
    utils.set_playbook_config_as_runtime_properties(ctx, kwargs)


def secure_log_playbook_args(_ctx, args, **_):
    """
    This function takes playbook_args and check against sensitive_keys
    to hide that sensitive values when logging
    """
    def _log(data, sensitive_keys, log_message="", hide=False):
        for key in data:
            hide = key in sensitive_keys
            value = data[key]
            if isinstance(value, dict):
                inner_log_message = "{0} : \n".format(key)
                lines = [s for s in
                         _log(value, sensitive_keys, '', hide).splitlines()
                         if s.strip()]
                for line in lines:
                    k, v = line.split(":", 1)[0], line.split(":", 1)[1]
                    hide = hide or (k in sensitive_keys)
                    inner_log_message += "  {0} : {1}\n".format(k,
                                                                '*'*len(v)
                                                                if hide else v)
                log_message += inner_log_message
            else:
                log_message += "{0} : {1}\n".format(key, '*'*len(value)
                                                         if hide else value)
        return log_message

    log_message = _log(args, args.get("sensitive_keys", {}))
    _ctx.logger.debug("playbook_args: \n {0}".format(log_message))


@operation(resumable=True)
@ansible_playbook_node
def run(playbook_args, ansible_env_vars, _ctx, **_):
    secure_log_playbook_args(_ctx, playbook_args)

    try:
        playbook = AnsiblePlaybookFromFile(**playbook_args)
        utils.assign_environ(ansible_env_vars)
        process = {}
        process['env'] = ansible_env_vars
        process['args'] = playbook.process_args
        # Prepare the script which need to be run
        playbook.execute(
            process_execution,
            script_func=execute,
            script_path='ansible-playbook',
            ctx=_ctx,
            process=process
        )
    except CloudifyAnsibleSDKError as sdk_error:
        raise NonRecoverableError(sdk_error)
    except ProcessException as process_error:
        if process_error.exit_code in UNREACHABLE_CODES:
            raise OperationRetry(
                'One or more hosts are unreachable.')
        if process_error.exit_code not in SUCCESS_CODES:
            raise NonRecoverableError(
                'One or more hosts failed.')


@operation(resumable=True)
@ansible_relationship_source
def ansible_requires_host(new_sources_dict, _ctx, **_):
    utils.update_sources_from_target(new_sources_dict, _ctx)


@operation(resumable=True)
@ansible_relationship_source
def ansible_remove_host(new_sources_dict, _ctx, **_):
    utils.cleanup_sources_from_target(new_sources_dict, _ctx)
