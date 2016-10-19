# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from jsonschema.exceptions import ValidationError

from efu import utils

from ..utils import EFUTestCase, FileFixtureMixin, EnvironmentFixtureMixin


class UtilsTestCase(EnvironmentFixtureMixin, EFUTestCase):

    def setUp(self):
        self.addCleanup(self.remove_env_var, utils.CHUNK_SIZE_VAR)
        self.addCleanup(self.remove_env_var, utils.GLOBAL_CONFIG_VAR)
        self.addCleanup(self.remove_env_var, utils.LOCAL_CONFIG_VAR)
        self.addCleanup(self.remove_env_var, utils.SERVER_URL_VAR)

    def test_get_chunk_size_by_environment_variable(self):
        os.environ[utils.CHUNK_SIZE_VAR] = '1'
        observed = utils.get_chunk_size()
        self.assertEqual(observed, 1)

    def test_get_default_chunk_size(self):
        observed = utils.get_chunk_size()
        self.assertEqual(observed, utils.DEFAULT_CHUNK_SIZE)

    def test_get_server_url_by_environment_variable(self):
        os.environ[utils.SERVER_URL_VAR] = 'http://ossystems.com.br'
        observed = utils.get_server_url()
        self.assertEqual(observed, 'http://ossystems.com.br')

    def test_get_default_server_url(self):
        observed = utils.get_server_url()
        self.assertEqual(observed, utils.DEFAULT_SERVER_URL)

    def test_can_get_url_with_path(self):
        os.environ[utils.SERVER_URL_VAR] = 'http://ossystems.com.br'
        observed = utils.get_server_url('/test')
        self.assertEqual(observed, 'http://ossystems.com.br/test')

    def test_yes_or_no_returns_yes_if_true(self):
        expected = 'yes'
        observed = utils.yes_or_no(True)
        self.assertEqual(expected, observed)

    def test_yes_or_no_returns_no_if_false(self):
        expected = 'no'
        observed = utils.yes_or_no(False)
        self.assertEqual(expected, observed)

    def test_can_get_default_global_config_file(self):
        observed = utils.get_global_config_file()
        self.assertEqual(observed, utils.DEFAULT_GLOBAL_CONFIG_FILE)

    def test_can_get_config_file_by_environment_variable(self):
        os.environ[utils.GLOBAL_CONFIG_VAR] = '/tmp/super_file'
        observed = utils.get_global_config_file()
        self.assertEqual(observed, '/tmp/super_file')


class LocalConfigTestCase(
        EnvironmentFixtureMixin, FileFixtureMixin, EFUTestCase):

    def setUp(self):
        self.config_fn = '/tmp/.efu'
        os.environ[utils.LOCAL_CONFIG_VAR] = self.config_fn
        self.addCleanup(self.remove_env_var, utils.LOCAL_CONFIG_VAR)
        self.addCleanup(self.remove_file, self.config_fn)

    def test_can_get_local_config_file_by_environment_variable(self):
        observed = utils.get_local_config_file()
        self.assertEqual(observed, '/tmp/.efu')

    def test_can_get_default_local_config_file(self):
        del os.environ[utils.LOCAL_CONFIG_VAR]
        observed = utils.get_local_config_file()
        self.assertEqual(observed, utils.DEFAULT_LOCAL_CONFIG_FILE)

    def test_can_load_local_config(self):
        with open(self.config_fn, 'w') as fp:
            fp.write('{"test": 42}')
        config = utils.get_local_config()
        self.assertEqual(config['test'], 42)

    def test_can_remove_package_file(self):
        open(self.config_fn, 'w').close()
        self.assertTrue(os.path.exists(self.config_fn))
        utils.remove_local_config()
        self.assertFalse(os.path.exists(self.config_fn))

    def test_remove_package_file_raises_error_when_file_already_deleted(self):
        self.assertFalse(os.path.exists(self.config_fn))
        with self.assertRaises(FileNotFoundError):
            utils.remove_local_config()


class MetadataValidatorTestCase(FileFixtureMixin, EFUTestCase):

    def setUp(self):
        self.schema = self.create_file(json.dumps({
            'type': 'object',
            'properties': {
                'test': {
                    'type': 'string',
                }
            },
            'additionalProperties': False,
            'required': ['test']
        }).encode())

    def test_validate_returns_None_when_valid(self):
        obj = {'test': 'ok'}
        self.assertIsNone(utils.validate_schema(self.schema, obj))

    def test_validate_raises_error_when_invalid(self):
        with self.assertRaises(ValidationError):
            utils.validate_schema(self.schema, {})
        with self.assertRaises(ValidationError):
            utils.validate_schema(self.schema, {'test': 1})
        with self.assertRaises(ValidationError):
            utils.validate_schema(self.schema, {'test': 'ok', 'extra': 2})


class CompressedObjectTestCase(FileFixtureMixin, EFUTestCase):

    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self.fixtures_dir = os.path.join(base_dir, '../fixtures/compressed/')
        uncompressed_fn = os.path.join(self.fixtures_dir, 'base.txt')
        self.size = os.path.getsize(uncompressed_fn)

    def test_can_get_gzip_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.gz')
        observed = utils.gzip_uncompressed_size(fn)
        self.assertEqual(observed, self.size)

    def test_can_get_lzma_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.xz')
        observed = utils.lzma_uncompressed_size(fn)
        self.assertEqual(observed, self.size)

    def test_can_get_lzo_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'base.txt.lzo')
        observed = utils.lzo_uncompressed_size(fn)
        self.assertEqual(observed, self.size)

    def test_can_get_tar_uncompressed_size(self):
        fn = os.path.join(self.fixtures_dir, 'archive.tar.gz')
        observed = utils.gzip_uncompressed_size(fn)
        expected = os.path.getsize(
            os.path.join(self.fixtures_dir, 'archive.tar'))
        self.assertEqual(observed, expected)

    def test_can_get_uncompressed_size(self):
        fixtures = ['base.txt.gz', 'base.txt.xz', 'base.txt.lzo']
        for fixture in fixtures:
            fn = os.path.join(self.fixtures_dir, fixture)
            observed = utils.get_uncompressed_size(fn)
            self.assertEqual(observed, self.size)

    def test_uncompressed_size_raises_error_if_invalid_file(self):
        fn = os.path.join(self.fixtures_dir, 'archive.tar')
        with self.assertRaises(ValueError):
            utils.get_uncompressed_size(fn)
