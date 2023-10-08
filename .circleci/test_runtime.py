########
# Copyright (c) 2014-2019 Cloudify Platform Ltd. All rights reserved
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

from os import environ
from contextlib import contextmanager

from ecosystem_tests.dorkl.constansts import logger
from ecosystem_tests.nerdl.api import (
    with_client,
    get_node_instance,
    wait_for_workflow,
    cleanup_on_failure,
    list_node_instances)

TEST_ID = environ.get('__ECOSYSTEM_TEST_ID', 'hello-world-example')


@contextmanager
def test_cleaner_upper():
    try:
        yield
    except Exception:
        cleanup_on_failure(TEST_ID)
        raise


def test_runtime_properties():
    with test_cleaner_upper():
        errors = []
        helloworld = node_instance_by_name('hello-world')
        logger.info('hello-world: {}'.format(helloworld))
        prop = helloworld['runtime_properties'].get('hello')
        if prop != 'world':
            errors.append(
                'Expected prop "hello" value to be "world", it is {}.'.format(
                    prop))
        if errors:
            error_messages = '\n'.join(errors)
            raise EcosystemTestException(
                'validate_runtime_properties failed because of {}'.format(
                    error_messages))


def node_instance_by_name(name):
    for node_instance in list_node_instances(TEST_ID):
        if node_instance['node_id'] == name:
            return get_node_instance(node_instance['id'])
    raise Exception('No node instances found.')
