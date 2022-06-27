
PLAYBOOK_ARGS_PROPS = [
    'ansible_playbook_executable_path', 'extra_packages', 'galaxy_collections',
    'playbook_source_path', 'playbook_path', 'site_yaml_path', 'save_playbook',
    'remerge_sources', 'sources', 'run_data', 'sensitive_keys', 'store_facts',
    'options_config', 'ansible_env_vars', 'debug_level', 'additional_args',
    'start_at_task', 'scp_extra_args', 'sftp_extra_args', 'ssh_common_args',
    'ssh_extra_args', 'timeout', 'auto_tags', 'number_of_attempts', 'tags',
]


def _ansible_operation(ctx, operation, node_ids, node_instance_ids, **kwargs):
    # pop empty values
    valid_kwargs = {}
    for key in kwargs:
        if kwargs[key]:
            valid_kwargs[key] = kwargs[key]

    graph = ctx.graph_mode()
    sequence = graph.sequence()
    # Iterate over all node instances of type "cloudify.nodes.ansible.Playbook"
    # or "cloudify.nodes.ansible.Executor"
    # and reload that playbook.
    operation_args = {
        'operation': operation,
        'kwargs': valid_kwargs,
        'allow_kwargs_override': True,
    }

    for node_instance in ctx.node_instances:
        if node_ids and (node_instance.node.id not in node_ids):
            continue
        if node_instance_ids and (node_instance.id not in node_instance_ids):
            continue
        if 'cloudify.nodes.ansible.Playbook' in \
            node_instance.node.type_hierarchy or \
            'cloudify.nodes.ansible.Executor' in \
                node_instance.node.type_hierarchy:
            add_previous_parameters(ctx, operation_args, node_instance)
            sequence.add(node_instance.execute_operation(**operation_args))
    return graph


def add_previous_parameters(ctx, operation_args, node_instance):
    ctx.logger.info('operation_args: {}'.format(operation_args))
    kwargs = operation_args.get('kwargs')
    ctx.logger.info('** 1kwargs: {}'.format(kwargs))

    for possible_key in PLAYBOOK_ARGS_PROPS:
        if not kwargs.get(possible_key) and \
                possible_key in \
                node_instance._node_instance.runtime_properties:
            ctx.logger.info('** possible_key: {}'.format(possible_key))
            kwargs[possible_key] = \
                node_instance._node_instance.runtime_properties[possible_key]
    operation_args['kwargs'] = kwargs
    ctx.logger.info('** 2kwargs: {}'.format(kwargs))


def reload_playbook(ctx, node_ids, node_instance_ids, **kwargs):
    _ansible_operation(ctx,
                       "ansible.reload",
                       node_ids,
                       node_instance_ids,
                       **kwargs).execute()
