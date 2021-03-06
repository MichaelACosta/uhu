# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import hashlib
import os
import tempfile
import unittest

from uhu.core import install_condition as ic
from uhu.core.install_condition import (
    normalize_install_if_different, KNOWN_PATTERNS, InstallCondition)
from uhu.core.object import Object

from utils import FileFixtureMixin, UHUTestCase


def create_u_boot_file():
    with tempfile.NamedTemporaryFile(delete=False) as fp:
        # U-Boot 13.08.1988 (13/08/1988)
        fp.write(bytearray.fromhex(
            '01552d426f6f742031332e30382e31393838202831332f30382f313938382902'))  # nopep8
    return fp.name


def create_u_boot_spl_file():
    with tempfile.NamedTemporaryFile(delete=False) as fp:
        # U-Boot SPL 13.08.1988 (13/08/1988)
        fp.write(bytearray.fromhex(
            '01552d426f6f742053504c2031332e30382e31393838202831332f30382f313938382902'))  # nopep8
    return fp.name


class KernelVersionTestCase(unittest.TestCase):

    def get_kernel_fixture(self, fixture):
        return os.path.join(
            'tests/core/fixtures/install-condition/kernel', fixture)

    def test_can_get_kernel_version(self):
        images = [
            ('arm-zImage', '4.4.1'),
            ('arm-uImage', '4.1.15-1.2.0+g274a055'),
            ('x86-bzImage', '4.1.30-1-MANJARO'),
            ('x86-zImage', '4.1.30-1-MANJARO'),
        ]
        for image, version in images:
            with open(self.get_kernel_fixture(image), 'br') as fp:
                observed = ic.get_kernel_version(fp)
                self.assertEqual(observed, version)

    def test_can_get_kernel_version_raises_error_if_cant_find_version(self):
        with tempfile.TemporaryFile() as fp:
            with self.assertRaises(ValueError):
                ic.get_kernel_version(fp)

    def test_is_arm_uImage_returns_True_when_arm_uImage(self):
        with open(self.get_kernel_fixture('arm-uImage'), 'br') as fp:
            self.assertTrue(ic.is_arm_u_image(fp))

    def test_is_arm_zImage_returns_True_when_arm_zImage(self):
        with open(self.get_kernel_fixture('arm-zImage'), 'br') as fp:
            self.assertTrue(ic.is_arm_z_image(fp))

    def test_is_x86_bzImage_returns_True_when_x86_bzImage(self):
        with open(self.get_kernel_fixture('x86-bzImage'), 'br') as fp:
            self.assertTrue(ic.is_x86_bz_image(fp))

    def test_is_x86_zImage_magic_returns_True_when_x86_zImage(self):
        with open(self.get_kernel_fixture('x86-zImage'), 'br') as fp:
            self.assertTrue(ic.is_x86_z_image(fp))

    def test_is_arm_uImage_returns_False_when_not_arm_uImage(self):
        images = ['arm-zImage', 'x86-bzImage', 'x86-zImage']
        for image in images:
            with open(self.get_kernel_fixture(image), 'rb') as fp:
                self.assertFalse(ic.is_arm_u_image(fp))

    def test_is_arm_zImage_returns_False_when_not_arm_zImage(self):
        images = ['arm-uImage', 'x86-bzImage', 'x86-zImage']
        for image in images:
            with open(self.get_kernel_fixture(image), 'rb') as fp:
                self.assertFalse(ic.is_arm_z_image(fp))

    def test_is_x86_bzImage_returns_False_when_not_x86_bzImage(self):
        images = ['arm-uImage', 'arm-zImage', 'x86-zImage']
        for image in images:
            with open(self.get_kernel_fixture(image), 'rb') as fp:
                self.assertFalse(ic.is_x86_bz_image(fp))

    def test_is_x86_zImage_magic_returns_False_when_not_x86_zImage(self):
        images = ['arm-uImage', 'arm-zImage', 'x86-bzImage']
        for image in images:
            with open(self.get_kernel_fixture(image), 'rb') as fp:
                self.assertFalse(ic.is_x86_z_image(fp))

    def test_can_get_arm_zImage_version(self):
        expected = '4.4.1'
        with open(self.get_kernel_fixture('arm-zImage'), 'br') as fp:
            observed = ic.get_arm_z_image_version(fp)
            self.assertEqual(expected, observed)

    def test_can_get_arm_uImage_version(self):
        expected = '4.1.15-1.2.0+g274a055'
        with open(self.get_kernel_fixture('arm-uImage'), 'br') as fp:
            observed = ic.get_arm_u_image_version(fp)
            self.assertEqual(expected, observed)

    def test_can_get_x86_bzImage_version(self):
        expected = '4.1.30-1-MANJARO'
        with open(self.get_kernel_fixture('x86-bzImage'), 'br') as fp:
            observed = ic.get_x86_bz_image_version(fp)
            self.assertEqual(expected, observed)

    def test_can_get_x86_zImage_version(self):
        expected = '4.1.30-1-MANJARO'
        with open(self.get_kernel_fixture('x86-zImage'), 'br') as fp:
            observed = ic.get_x86_z_image_version(fp)
            self.assertEqual(expected, observed)


class UBootVersionTestCase(unittest.TestCase):

    def test_can_get_uboot_version(self):
        fn = create_u_boot_file()
        self.addCleanup(os.remove, fn)
        expected = '13.08.1988'
        with open(fn, 'br') as fp:
            observed = ic.get_uboot_version(fp)
            self.assertEqual(observed, expected)

    def test_can_get_uboot_spl_version(self):
        fn = create_u_boot_spl_file()
        self.addCleanup(os.remove, fn)
        expected = '13.08.1988'
        with open(fn, 'br') as fp:
            observed = ic.get_uboot_version(fp)
            self.assertEqual(observed, expected)

    def test_get_uboot_version_raises_error_if_cant_find_version(self):
        with tempfile.TemporaryFile() as fp:
            with self.assertRaises(ValueError):
                ic.get_uboot_version(fp)


class CustomObjectVersionTestCase(unittest.TestCase):

    def test_can_get_custom_object_version(self):
        fp = tempfile.TemporaryFile()
        self.addCleanup(fp.close)
        fp.write(bytearray.fromhex('5f5f5f312e305f5f5f'))  # ___1.0___
        expected = '1.0'
        observed = ic.get_object_version(fp, br'\d\.\d', seek=3, buffer_size=5)
        self.assertEqual(observed, expected)

    def test_get_object_version_raises_error_if_cant_find_version(self):
        with tempfile.TemporaryFile() as fp:
            with self.assertRaises(ValueError):
                ic.get_object_version(fp, br'^unfindable$')


class AlwaysObjectIntegrationTestCase(FileFixtureMixin, UHUTestCase):

    def setUp(self):
        super().setUp()
        self.fn = self.create_file(b'spam')
        self.options = {
            'filename': self.fn,
            'mode': 'raw',
            'install-condition': 'always',
            'target-type': 'device',
            'target': '/dev/sda',
        }

    def test_can_create_object(self):
        obj = Object(self.options)
        self.assertEqual(obj['install-condition'], 'always')

    def test_can_represent_as_template(self):
        obj = Object(self.options)
        expected = {
            'filename': self.fn,
            'mode': 'raw',
            'chunk-size': 131072,
            'count': -1,
            'seek': 0,
            'skip': 0,
            'target-type': 'device',
            'target': '/dev/sda',
            'truncate': False,
            'install-condition': 'always',
        }
        observed = obj.to_template()
        self.assertEqual(observed, expected)

    def test_can_represent_as_metadata(self):
        obj = Object(self.options)
        expected = {
            'filename': self.fn,
            'mode': 'raw',
            'chunk-size': 131072,
            'count': -1,
            'seek': 0,
            'skip': 0,
            'target-type': 'device',
            'target': '/dev/sda',
            'truncate': False,
            'size': 4,
            'sha256sum': hashlib.sha256(b'spam').hexdigest(),
        }
        observed = obj.to_metadata()
        self.assertEqual(observed, expected)


class ContentDivergesObjectIntegrationTestCase(FileFixtureMixin, UHUTestCase):

    def setUp(self):
        super().setUp()
        self.fn = self.create_file(b'spam')
        self.options = {
            'filename': self.fn,
            'mode': 'raw',
            'install-condition': 'content-diverges',
            'target-type': 'device',
            'target': '/dev/sda',
        }

    def test_can_create_object(self):
        obj = Object(self.options)
        self.assertEqual(obj['install-condition'], 'content-diverges')

    def test_can_represent_as_template(self):
        obj = Object(self.options)
        expected = {
            'filename': self.fn,
            'mode': 'raw',
            'chunk-size': 131072,
            'count': -1,
            'seek': 0,
            'skip': 0,
            'target-type': 'device',
            'target': '/dev/sda',
            'truncate': False,
            'install-condition': 'content-diverges',
        }
        observed = obj.to_template()
        self.assertEqual(observed, expected)

    def test_can_represent_as_metadata(self):
        obj = Object(self.options)
        expected = {
            'filename': self.fn,
            'mode': 'raw',
            'chunk-size': 131072,
            'count': -1,
            'seek': 0,
            'skip': 0,
            'target-type': 'device',
            'target': '/dev/sda',
            'truncate': False,
            'size': 4,
            'sha256sum': hashlib.sha256(b'spam').hexdigest(),
            'install-if-different': 'sha256sum'
        }
        observed = obj.to_metadata()
        self.assertEqual(observed, expected)


class KnownVersionPatternObjectIntegrationTestCase(unittest.TestCase):

    def setUp(self):
        current_dir = os.getcwd()
        self.addCleanup(os.chdir, current_dir)
        os.chdir('tests/core/fixtures/install-condition/kernel')

        self.images = [
            ('arm-zImage', '4.4.1'),
            ('arm-uImage', '4.1.15-1.2.0+g274a055'),
            ('x86-bzImage', '4.1.30-1-MANJARO'),
            ('x86-zImage', '4.1.30-1-MANJARO'),
        ]
        self.options = {
            'filename': __file__,
            'mode': 'raw',
            'install-condition': 'version-diverges',
            'install-condition-pattern-type': None,  # to be replaced by tests
            'target-type': 'device',
            'target': '/dev/sda'
        }
        self.template = {
            'filename': None,  # to be replaced by tests
            'mode': 'raw',
            'chunk-size': 131072,
            'count': -1,
            'seek': 0,
            'skip': 0,
            'target-type': 'device',
            'target': '/dev/sda',
            'truncate': False,
            'install-condition': 'version-diverges',
            # to be replaced by tests
            'install-condition-pattern-type': None,
        }
        self.metadata = {
            'filename': None,  # to be replaced by tests
            'mode': 'raw',
            'chunk-size': 131072,
            'count': -1,
            'seek': 0,
            'skip': 0,
            'target-type': 'device',
            'target': '/dev/sda',
            'truncate': False,
            'size': None,  # to be replaced by tests
            'sha256sum': None,  # to be replaced by tests
            'install-if-different': {
                'version': None,  # to be replaced by tests
                'pattern': None,  # to be replaced by tests
            }
        }

    def test_can_create_linux_kernel_object(self):
        self.options['install-condition-pattern-type'] = 'linux-kernel'
        obj = Object(self.options)
        self.assertEqual(obj['install-condition'], 'version-diverges')
        self.assertEqual(obj['install-condition-pattern-type'], 'linux-kernel')
        self.assertIsNone(obj['install-condition-version'])

    def test_can_create_uboot_object(self):
        self.options['install-condition-pattern-type'] = 'u-boot'
        obj = Object(self.options)
        self.assertEqual(obj['install-condition'], 'version-diverges')
        self.assertEqual(obj['install-condition-pattern-type'], 'u-boot')
        self.assertIsNone(obj['install-condition-version'])

    def test_can_load_linux_kernel_versions(self):
        for image, version in self.images:
            self.options['install-condition-pattern-type'] = 'linux-kernel'
            self.options['install-condition'] = 'version-diverges'
            self.options['filename'] = image
            obj = Object(self.options)
            metadata = obj.to_metadata()
            self.assertEqual(
                metadata['install-if-different']['version'], version)

    def test_can_load_u_boot_version(self):
        self.options['install-condition-pattern-type'] = 'u-boot'
        self.options['filename'] = create_u_boot_file()
        obj = Object(self.options)
        metadata = obj.to_metadata()
        self.assertEqual(
            metadata['install-if-different']['version'], '13.08.1988')

    def test_can_represent_linux_kernel_object_as_template(self):
        self.options['install-condition-pattern-type'] = 'linux-kernel'
        self.template['install-condition-pattern-type'] = 'linux-kernel'  # nopep8
        self.template['filename'] = __file__
        obj = Object(self.options)
        self.assertEqual(obj.to_template(), self.template)

    def test_can_represent_u_boot_object_as_template(self):
        self.options['install-condition-pattern-type'] = 'u-boot'
        self.template['install-condition-pattern-type'] = 'u-boot'
        self.template['filename'] = __file__
        obj = Object(self.options)
        self.assertEqual(obj.to_template(), self.template)

    def test_can_represent_linux_kernel_object_as_metadata(self):
        self.metadata['install-if-different']['pattern'] = 'linux-kernel'
        for image, version in self.images:
            self.options['filename'] = image
            self.options['install-condition'] = 'version-diverges'
            self.options['install-condition-pattern-type'] = 'linux-kernel'
            self.metadata['install-if-different']['version'] = version
            self.metadata['filename'] = image
            self.metadata['size'] = os.path.getsize(image)
            with open(image, 'rb') as fp:
                sha256sum = hashlib.sha256(fp.read()).hexdigest()
                self.metadata['sha256sum'] = sha256sum
                obj = Object(self.options)
                self.assertEqual(obj.to_metadata(), self.metadata)

    def test_can_represent_u_boot_object_as_metadata(self):
        fn = create_u_boot_file()
        self.options['filename'] = fn
        self.options['install-condition-pattern-type'] = 'u-boot'
        self.metadata['install-if-different']['pattern'] = 'u-boot'
        self.metadata['install-if-different']['version'] = '13.08.1988'
        self.metadata['filename'] = fn
        self.metadata['size'] = os.path.getsize(fn)
        with open(fn, 'rb') as fp:
            sha256sum = hashlib.sha256(fp.read()).hexdigest()
            self.metadata['sha256sum'] = sha256sum
            obj = Object(self.options)
            self.assertEqual(obj.to_metadata(), self.metadata)


class CustomVersionPatternObjectIntegrationTestCase(
        FileFixtureMixin, UHUTestCase):

    def setUp(self):
        super().setUp()
        version = '5f5f5f312e305f5f5f'  # ___1.0___
        self.content = bytes(bytearray.fromhex(version))
        self.fn = self.create_file(self.content)
        self.options = {
            'filename': self.fn,
            'mode': 'raw',
            'install-condition': 'version-diverges',
            'install-condition-pattern-type': 'regexp',
            'install-condition-pattern': '\d+\.\d+',
            'install-condition-seek': 3,
            'install-condition-buffer-size': 5,
            'target-type': 'device',
            'target': '/dev/sda',
        }
        self.template = {
            'filename': self.fn,
            'mode': 'raw',
            'chunk-size': 131072,
            'count': -1,
            'seek': 0,
            'skip': 0,
            'target-type': 'device',
            'target': '/dev/sda',
            'truncate': False,
            'install-condition': 'version-diverges',
            'install-condition-pattern-type': 'regexp',
            'install-condition-pattern': '\d+\.\d+',
            'install-condition-seek': 3,
            'install-condition-buffer-size': 5,
        }
        self.metadata = {
            'filename': self.fn,
            'mode': 'raw',
            'chunk-size': 131072,
            'count': -1,
            'seek': 0,
            'skip': 0,
            'target-type': 'device',
            'target': '/dev/sda',
            'truncate': False,
            'size': len(self.content),
            'sha256sum': hashlib.sha256(self.content).hexdigest(),
            'install-if-different': {
                'version': '1.0',
                'pattern': {
                    'regexp': '\d+\.\d+',
                    'seek': 3,
                    'buffer-size': 5,
                }
            }
        }

    def test_can_create_object(self):
        obj = Object(self.options)
        self.assertEqual(obj['install-condition'], 'version-diverges')
        self.assertEqual(obj['install-condition-pattern-type'], 'regexp')
        self.assertEqual(obj['install-condition-pattern'], '\d+\.\d+')
        self.assertEqual(obj['install-condition-seek'], 3)
        self.assertEqual(obj['install-condition-buffer-size'], 5)
        self.assertIsNone(obj['install-condition-version'])

    def test_can_load_custom_object_version(self):
        obj = Object(self.options)
        metadata = obj.to_metadata()
        self.assertEqual(metadata['install-if-different']['version'], '1.0')

    def test_can_represent_as_template(self):
        obj = Object(self.options)
        self.assertEqual(obj.to_template(), self.template)

    def test_can_represent_as_metadata(self):
        obj = Object(self.options)
        self.assertEqual(obj.to_metadata(), self.metadata)


class InstallConditionRepresentationTestCase(unittest.TestCase):

    def setUp(self):
        cwd = os.getcwd()
        os.chdir('tests/core/fixtures/install-condition')
        self.addCleanup(os.chdir, cwd)

    def get_fixture(self, fn):
        with open(fn) as fp:
            return fp.read().strip()

    def test_object_with_install_condition_always(self):
        expected = self.get_fixture('install_condition_always.txt')
        obj = Object({
            'filename': 'file.txt',
            'mode': 'raw',
            'target-type': 'device',
            'target': '/',
            'install-condition': 'always',
        })
        self.assertEqual(str(obj), expected)

    def test_object_with_install_condition_content_diverges(self):
        expected = self.get_fixture('install_condition_content.txt')
        obj = Object({
            'filename': 'file.txt',
            'mode': 'raw',
            'target-type': 'device',
            'target': '/',
            'install-condition': 'content-diverges',
        })
        self.assertEqual(str(obj), expected)

    def test_object_with_install_condition_known_version_diverges(self):
        expected = self.get_fixture('install_condition_known_version.txt')
        obj = Object({
            'filename': 'file.txt',
            'mode': 'raw',
            'target-type': 'device',
            'target': '/',
            'install-condition': 'version-diverges',
            'install-condition-pattern-type': 'linux-kernel',
        })
        self.assertEqual(str(obj), expected)

    def test_object_with_install_condition_regexp_version_diverges(self):
        expected = self.get_fixture('install_condition_version_regexp.txt')
        obj = Object({
            'filename': 'file.txt',
            'mode': 'raw',
            'target-type': 'device',
            'target': '/',
            'install-condition': 'version-diverges',
            'install-condition-pattern-type': 'regexp',
            'install-condition-pattern': '.+',
            'install-condition-seek': 0,
            'install-condition-buffer-size': 100,
        })
        self.assertEqual(str(obj), expected)

    def test_object_without_install_condition_support(self):
        obj = Object({
            'filename': 'file.txt',
            'mode': 'ubifs',
            'target-type': 'ubivolume',
            'target': 'system0',
        })
        expected = self.get_fixture('install_condition_ubifs.txt')
        self.assertEqual(str(obj), expected)


class InstallIfDifferentNormalizationTestCase(unittest.TestCase):

    def make_iid(self, iid):
        return {'install-if-different': iid}

    def test_can_convert_when_iid_is_None(self):
        observed = normalize_install_if_different({})
        self.assertEqual(observed, {})

    def test_can_convert_when_iid_is_sha256sum(self):
        observed = normalize_install_if_different(self.make_iid('sha256sum'))
        self.assertEqual(observed, {
            'install-condition': 'content-diverges',
        })

    def test_normalizer_raises_error_if_not_object_or_sha256sum(self):
        with self.assertRaises(TypeError):
            normalize_install_if_different(self.make_iid(42))

    def test_normalizer_raises_error_if_missing_version(self):
        with self.assertRaises(ValueError):
            normalize_install_if_different(self.make_iid({}))

    def test_can_convert_when_known_pattern(self):
        for pattern in KNOWN_PATTERNS:
            observed = normalize_install_if_different(self.make_iid({
                'version': '2.0',
                'pattern': pattern,
            }))
            self.assertEqual(observed, {
                'install-condition': 'version-diverges',
                'install-condition-version': '2.0',
                'install-condition-pattern-type': pattern,
            })

    def test_can_convert_when_custom_pattern(self):
        observed = normalize_install_if_different(self.make_iid({
            'version': '2.0',
            'pattern': {
                'regexp': 'spam',
                'seek': 42,
                'buffer-size': 42
            },
        }))
        self.assertEqual(observed, {
            'install-condition': 'version-diverges',
            'install-condition-version': '2.0',
            'install-condition-seek': 42,
            'install-condition-buffer-size': 42,
            'install-condition-pattern-type': 'regexp',
            'install-condition-pattern': 'spam',
        })

    def test_raises_error_if_missing_regexp(self):
        with self.assertRaises(ValueError):
            normalize_install_if_different(self.make_iid({
                'version': '2.0',
                'pattern': {},
            }))


class InstallConditionToMetadataTestCase(unittest.TestCase):

    def test_raises_error_if_invalid_condition(self):
        invalid_conditions = [None, 1, 'unknown', 'grub']
        for condition in invalid_conditions:
            with self.assertRaises(ValueError):
                obj = {
                    'filename': __file__,
                    'install-condition': condition,
                }
                InstallCondition(obj).to_metadata()

    def test_raises_error_if_invalid_pattern(self):
        invalid_patterns = [None, 1, 'unknown', 'grub']
        for pattern in invalid_patterns:
            with self.assertRaises(ValueError):
                obj = {
                    'filename': __file__,
                    'install-condition': InstallCondition.VERSION_DIVERGES,
                    'install-condition-pattern-type': pattern,
                }
                InstallCondition(obj).to_metadata()
