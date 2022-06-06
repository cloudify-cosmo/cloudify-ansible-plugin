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
            sequence.add(node_instance.execute_operation(**operation_args))
    return graph


def reload_playbook(ctx, node_ids, node_instance_ids, **kwargs):
    _ansible_operation(ctx,
                       "ansible.reload",
                       node_ids,
                       node_instance_ids,
                       **kwargs).execute()
