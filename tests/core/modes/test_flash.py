# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

from utils import UHUTestCase
from .base import ModeTestCaseMixin


class FlashObjectTestCase(ModeTestCaseMixin, UHUTestCase):
    mode = 'flash'

    def setUp(self):
        super().setUp()
        self.default_options = {
            'filename': self.fn,
            'mode': self.mode,
            'target-type': 'device',
            'target': '/dev/sda'
        }
        self.default_template = {
            'filename': self.fn,
            'mode': 'flash',
            'install-condition': 'always',
            'target-type': 'device',
            'target': '/dev/sda',
        }
        self.default_metadata = {
            'filename': self.fn,
            'mode': 'flash',
            'sha256sum': self.sha256sum,
            'size': self.size,
            'target-type': 'device',
            'target': '/dev/sda'
        }

        self.full_options = {
            'filename': self.fn,
            'mode': self.mode,
            'target-type': 'device',
            'target': '/dev/sda',
            'install-condition': 'always',
            'install-condition-pattern-type': None,
            'install-condition-pattern': None,
            'install-condition-seek': None,
            'install-condition-buffer-size': None,
        }
        self.full_template = {
            'filename': self.fn,
            'mode': 'flash',
            'install-condition': 'always',
            'target-type': 'device',
            'target': '/dev/sda',
        }
        self.full_metadata = {
            'filename': self.fn,
            'mode': 'flash',
            'sha256sum': self.sha256sum,
            'size': self.size,
            'target-type': 'device',
            'target': '/dev/sda'
        }
