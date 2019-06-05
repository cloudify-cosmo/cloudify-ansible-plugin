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

import json
import logging
import os
import subprocess
import sys
from tempfile import mkdtemp, NamedTemporaryFile


DEPRECATED_KEYS = [
    'site_yaml_path',
    'inventory_config',
    'variable_manager_config',
    'passwords',
    'modules',
    'private_key_file']
LIST_TYPES = ['skip-tags', 'tags']


def get_fileno():
    try:
        return sys.stdout.fileno
    except AttributeError:
        return


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
      From here: https://stackoverflow.com/
      questions/11124093/redirect-python-print-output-to-logger/11124247.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''
        self.fileno = get_fileno()

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def read(self, size):
        msg = "Read action with size {size} is unsupported.".format(size=size)
        self.logger.log(self.log_level, msg)
        raise IOError(msg)

    def flush(self):
        pass


class CloudifyAnsibleSDKError(Exception):
    """Generic Error for handling issues preparing
    the Ansible Playbook.
    """

    pass


class AnsiblePlaybookFromFile(object):
    """ Object for communication to Ansible Library."""

    def __init__(self,
                 playbook_path=None,
                 sources='localhost,',
                 options_config=None,
                 run_data=None,
                 verbosity=2,
                 logger=None,
                 site_yaml_path=None,
                 environment_variables=None,
                 additional_args=None,
                 **kwargs):

        self.playbook = site_yaml_path or playbook_path
        self.sources = sources
        self.options_config = options_config or {}
        self.run_data = run_data or {}
        self.environment_variables = environment_variables or {}
        self.additional_args = additional_args or ''
        self._verbosity = verbosity
        self.logger = logger

        for deprecated_key in DEPRECATED_KEYS:
            if deprecated_key in kwargs:
                self.logger.error(
                    'This key been deprecated: {0} {1}'.format(
                        deprecated_key, kwargs[deprecated_key]))

    @property
    def env(self):
        _env = os.environ.copy()
        for key, value in self.environment_variables.items():
            _env[key] = value
        return _env

    @property
    def verbosity(self):
        verbosity = '-v'
        for i in range(1, self._verbosity):
            verbosity += 'v'
        return verbosity

    @property
    def options(self):
        options_list = []
        if 'extra_vars' not in self.options_config:
            self.options_config['extra_vars'] = {}
        self.options_config['extra_vars'].update(self.run_data)
        for key, value in self.options_config.items():
            if key == 'extra_vars':
                f = NamedTemporaryFile(delete=False)
                with open(f.name, 'w') as outfile:
                    json.dump(value, outfile)
                value = '@{filepath}'.format(filepath=f.name)
            elif key == 'verbosity':
                self.logger.error('No such option verbosity')
                del key
                continue
            key = key.replace("_", "-")
            if isinstance(value, basestring):
                value = value.encode('utf-8')
            elif isinstance(value, dict):
                value = json.dumps(value)
            elif isinstance(value, list) and key not in LIST_TYPES:
                value = [i.encode('utf-8') for i in value]
            elif isinstance(value, list):
                value = ",".join(value).encode('utf-8')
            options_list.append(
                '--{key}={value}'.format(key=key, value=repr(value)))
        return ' '.join(options_list)

    @property
    def command(self):
        return 'ansible-playbook {verbosity} ' \
               '-i {sources} ' \
               '{options} ' \
               '{additional_args} ' \
               '{playbook}'.format(verbosity=self.verbosity,
                                   sources=self.sources,
                                   options=self.options,
                                   additional_args=self.additional_args,
                                   playbook=self.playbook)

    def _execute(self):
        popen_args = {
            'args': self.command,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.STDOUT,
            'universal_newlines': True,
            'shell': True,
            'cwd': mkdtemp(),
            'env': self.env
        }
        self.logger.info('popen_args: {0}'.format(popen_args))
        proc = subprocess.Popen(**popen_args)
        for line in proc.stdout:
            self.logger.info(line)
        (output, error) = proc.communicate()
        return output, error, proc.returncode

    def execute(self, redirect_logs=True):
        _stdout = sys.stdout
        _stderr = sys.stderr
        _stdin = sys.stdin
        try:
            if redirect_logs:
                sys.stdout = StreamToLogger(self.logger, logging.INFO)
                sys.stderr = StreamToLogger(self.logger, logging.ERROR)
                sys.stdin = StreamToLogger(self.logger, logging.DEBUG)
            return self._execute()
        finally:
            sys.stdout = _stdout
            sys.stderr = _stderr
            sys.stdin = _stdin
