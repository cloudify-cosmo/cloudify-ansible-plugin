from cloudify import ctx
from cloudify.state import ctx_parameters as inputs


if __name__ == '__main__':
    ctx.logger.info('Start: we have these runtime props: {}'.format(
        ctx.instance.runtime_properties))
    properties = {}
    ctx.logger.info('Start: we got these inputs: {}'.format(inputs))
    if 'ctx' in inputs:
        del inputs['ctx']
    properties.update(inputs)
    properties.update(ctx.instance.runtime_properties)
    ctx.instance.runtime_properties = properties
    ctx.logger.info('End: we have these runtime props: {}'.format(
        ctx.instance.runtime_properties))
