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

from cloudify import ctx as ctx_from_import

from cloudify_ansible.utils import (
    create_playbook_workspace,
    delete_playbook_workspace,
    handle_site_yaml,
    handle_sources
)


def playbook_and_sources(func):

    def wrapper(site_yaml_path, sources, ctx=ctx_from_import, **kwargs):

        create_playbook_workspace(ctx)
        site_yaml_path = handle_site_yaml(site_yaml_path, ctx)
        playbook_args = {
            'site_yaml_path': site_yaml_path,
            'sources': handle_sources(sources, site_yaml_path, ctx),
            'verbosity': 2
        }
        playbook_args.update(**kwargs)
        func(playbook_args, ctx)
        delete_playbook_workspace(ctx)

    return wrapper
