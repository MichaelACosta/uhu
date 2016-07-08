# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json

from . import exceptions
from .file import File


class Package(object):

    def __init__(self, package):
        self._package = self._validate_package(package)
        self.product_id = self._package.get('product_id')
        self.files = {}
        for fn in self._package.get('files'):
            file = File(fn)
            self.files[file.id] = file

    def _validate_package(self, filename):
        try:
            with open(filename) as fp:
                package = json.load(fp)
        except FileNotFoundError:
            raise exceptions.InvalidPackageFileError(
                '{} file does not exist'.format(filename)
            )
        except ValueError:
            raise exceptions.InvalidPackageFileError(
                '{} is not a valid JSON file'.format(filename)
            )
        return package

    def as_dict(self):
        return {
            'objects': [file.as_dict() for file in self.files.values()]
        }
