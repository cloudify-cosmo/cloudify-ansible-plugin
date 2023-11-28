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
import sys
import pathlib

from setuptools import setup, find_packages


def get_version():
    current_dir = pathlib.Path(__file__).parent.resolve()

    with open(os.path.join(current_dir, 'cloudify_ansible/__version__.py'),
              'r') as outfile:
        var = outfile.read()
        return re.search(r'\d+.\d+.\d+', var).group()


install_requires = [
    'ansible',
    'pexpect==4.8.0',
]

if sys.version_info.major == 3 and sys.version_info.minor == 6:
    packages = ['cloudify_ansible', 'cloudify_ansible_sdk']
    install_requires += [
        'cloudify-common>=4.5.5',
        'cloudify-utilities-plugins-sdk>=0.0.121',
    ]
else:
    packages = find_packages()
    install_requires += [
        'fusion-common',
        'cloudify-utilities-plugins-sdk',
    ]


setup(
    name='cloudify-ansible-plugin',
    version=get_version(),
    author='Cloudify Platform LTD',
    author_email='hello@cloudify.co',
    description='Manage Ansible nodes by Cloudify.',
    packages=packages,
    package_data={
        'cloudify_ansible': [
            'ansible-cloudify-ctx/modules/cloudify_runtime_property.py',
            'ansible/plugins/connection/winrm.py'
        ]
    },
    license='LICENSE',
    zip_safe=False,
    install_requires=install_requires
)
