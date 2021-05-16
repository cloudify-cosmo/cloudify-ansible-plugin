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
    RecoverableError,
    OperationRetry
)

from script_runner.tasks import (
    execute,
    ProcessException
)

from cloudify_ansible_sdk import (
    AnsiblePlaybookFromFile,
    CloudifyAnsibleSDKError
)
from cloudify_ansible import (
    ansible_playbook_node,
    ansible_relationship_source,
    utils,
    constants
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

    def _log(data, sensitive_keys, log_message="", parent_hide=False):
        """
        ::param data : dict to check againt sensitive_keys
        ::param sensitive_keys : a list of keys we want to hide the values for
        ::param log_message : a string to append the message to
        ::param parent_hide : boolean flag to pass if the parent key is
                              in sensitive_keys
        """
        for key in data:
            # check if key in sensitive_keys or parent_hide
            hide = parent_hide or (key in sensitive_keys)
            value = data[key]
            # handle dict value incase sensitive_keys was inside another key
            if isinstance(value, dict):
                # call _log function recusivly to handle the dict value
                log_message += "{0} : \n".format(key)
                v = _log(value, sensitive_keys, "", hide)
                log_message += "  {0}".format("  ".join(v.splitlines(True)))
            else:
                # if hide true hide the value with "*"
                log_message += "{0} : {1}\n".format(
                    key, '*' * len(value) if hide else value)
        return log_message

    log_message = _log(args, args.get("sensitive_keys", {}))
    _ctx.logger.debug("playbook_args: \n {0}".format(log_message))


@operation(resumable=True)
@ansible_playbook_node
def run(playbook_args, ansible_env_vars, _ctx, **kwargs):
    _node = utils.get_node(_ctx)
    _instance = utils.get_instance(_ctx)

    playbook_tags, tags = utils.get_playbook_args_tags(
        _node, _instance, playbook_args['playbook_path'])

    playbook_args['tags'] = playbook_tags

    secure_log_playbook_args(_ctx, playbook_args)
    playbook = AnsiblePlaybookFromFile(**playbook_args)
    # check if ansible_playbook_executable_path was provided
    # if not provided default to "ansible-playbook" which will use the
    # executable included in the temporary virtual env for the deployment.
    script_path = playbook_args.get("ansible_playbook_executable_path") or \
        utils.get_executable_path(
            executable="ansible-playbook",
            venv=utils.get_instance(
                _ctx).runtime_properties[constants.PLAYBOOK_VENV])
    utils.assign_environ(ansible_env_vars)
    process = dict()
    process['env'] = ansible_env_vars
    process['args'] = playbook.process_args

    try:
        playbook.execute(
            utils.process_execution,
            script_func=execute,
            script_path=script_path,
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
        else:
            raise RecoverableError('Retrying...')

    if constants.COMPLETED_TAGS not in _instance.runtime_properties:
        _instance.runtime_properties[constants.COMPLETED_TAGS] = \
            playbook_tags
    else:
        _instance.runtime_properties[constants.COMPLETED_TAGS].extend(
            playbook_tags)
    _instance.runtime_properties[constants.AVAILABLE_TAGS] = tags
    if tags:
        raise OperationRetry(
            'Waiting to perform all tags: {}'.format(
                _instance.runtime_properties[
                    constants.AVAILABLE_TAGS]))

    if 'establish' in _ctx.operation.name.split('.')[-1]:
        _store_facts(playbook, ansible_env_vars, _ctx, **kwargs)


def _store_facts(playbook, ansible_env_vars, _ctx, **_):
    utils.assign_environ(ansible_env_vars)
    process = dict()
    process['env'] = ansible_env_vars
    process['args'] = playbook.facts_args
    try:
        facts = playbook.get_facts(
            utils.process_execution,
            script_func=utils.execute_copy,
            script_path=utils.get_executable_path(
                executable="ansible",
                venv=utils.get_instance(
                    _ctx).runtime_properties[constants.PLAYBOOK_VENV]),
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
        else:
            raise RecoverableError('Retrying...')
    _node = utils.get_node(_ctx)
    _instance = utils.get_instance(_ctx)
    facts = utils.get_facts(facts)
    if _node.properties.get('store_facts', True):
        _instance.runtime_properties['facts'] = facts


@operation(resumable=True)
@ansible_playbook_node
def store_facts(playbook_args, ansible_env_vars, _ctx, **kwargs):
    secure_log_playbook_args(_ctx, playbook_args)
    playbook = AnsiblePlaybookFromFile(**playbook_args)
    _store_facts(playbook, ansible_env_vars, _ctx, **kwargs)


@operation(resumable=True)
@ansible_relationship_source
def ansible_requires_host(new_sources_dict, _ctx, **_):
    utils.update_sources_from_target(new_sources_dict, _ctx)


@operation(resumable=True)
@ansible_relationship_source
def ansible_remove_host(new_sources_dict, _ctx, **_):
    utils.cleanup_sources_from_target(new_sources_dict, _ctx)
