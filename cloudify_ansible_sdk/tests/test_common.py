# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
import unittest
import logging

import cloudify_ansible_sdk


class CommonTests(unittest.TestCase):

    def test_read(self):
        fake_log = mock.Mock()
        with self.assertRaisesRegexp(
            IOError,
            "Read action with size 10 is unsupported."
        ):
            stdio = cloudify_ansible_sdk.StreamToLogger(fake_log, logging.INFO)
            stdio.read(10)
        fake_log.log.assert_called_with(
            logging.INFO, 'Read action with size 10 is unsupported.')

    def test_flush(self):
        fake_log = mock.Mock()
        stdio = cloudify_ansible_sdk.StreamToLogger(fake_log, logging.INFO)
        stdio.flush()
        fake_log.log.assert_not_called()

    def test_write(self):
        fake_log = mock.Mock()
        stdio = cloudify_ansible_sdk.StreamToLogger(fake_log, logging.DEBUG)
        stdio.write("a\nb")
        fake_log.log.assert_has_calls([
            mock.call(logging.DEBUG, "a"),
            mock.call(logging.DEBUG, "b")
        ])
