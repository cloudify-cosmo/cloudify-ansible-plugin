def _ansible_operation(ctx, playbook_source_path, playbook_path, operation,
                       node_ids, node_instance_ids):
    graph = ctx.graph_mode()
    sequence = graph.sequence()
    # Iterate over all node instances of type "cloudify.nodes.ansible.Playbook"
    # or "cloudify.nodes.ansible.Executor"
    # and reload that playbook.
    operation_args = {
        'operation': operation,
        'kwargs': {
            'playbook_source_path': playbook_source_path,
            'playbook_path': playbook_path,
        },
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


def reload_playbook(ctx, playbook_source_path, playbook_path, node_ids,
                    node_instance_ids):
    _ansible_operation(ctx, playbook_source_path, playbook_path,
                       "ansible.reload",
                       node_ids,
                       node_instance_ids).execute()
