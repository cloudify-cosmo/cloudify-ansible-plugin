########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import os
import re
import pathlib

from setuptools import setup


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version():
    current_dir = pathlib.Path(__file__).parent.resolve()

    with open(os.path.join(current_dir, 'cloudify_ansible/__version__.py'),
              'r') as outfile:
        var = outfile.read()
        return re.search(r'\d+.\d+.\d+', var).group()


setup(
    name='cloudify-ansible-plugin',
    version=get_version(),
    author='Cloudify Platform LTD',
    author_email='hello@cloudify.co',
    description='Manage Ansible nodes by Cloudify.',
    packages=['cloudify_ansible', 'cloudify_ansible_sdk'],
    package_data={
        'cloudify_ansible': [
            'ansible-cloudify-ctx/modules/cloudify_runtime_property.py',
            'ansible/plugins/connection/winrm.py'
        ]
    },
    license='LICENSE',
    zip_safe=False,
    install_requires=[
        "cloudify-common>=4.5.5",
        "cloudify-utilities-plugins-sdk>=0.0.84",
        "ansible==4.10.0",
        "pexpect==4.8.0",
    ]
)
