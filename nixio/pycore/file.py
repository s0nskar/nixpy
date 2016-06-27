# Copyright (c) 2016, German Neuroinformatics Node (G-Node)
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted under the terms of the BSD License. See
# LICENSE file in the root of the Project.
from __future__ import (absolute_import, division, print_function)
import os

import h5py

from .h5group import H5Group
from .block import Block
from .exceptions import exceptions
from .section import Section
from ..file import FileMixin
from . import util

try:
    from ..core import File as CFile
except ImportError:
    CFile = None


class FileMode(object):
    ReadOnly = 'r'
    ReadWrite = 'a'
    Overwrite = 'w'


def map_file_mode(mode):
    if mode == FileMode.ReadOnly:
        return h5py.h5f.ACC_RDONLY
    elif mode == FileMode.ReadWrite:
        return h5py.h5f.ACC_RDWR
    elif mode == FileMode.Overwrite:
        return h5py.h5f.ACC_TRUNC
    else:
        ValueError("Invalid file mode specified.")


def make_fapl():
    return h5py.h5p.create(h5py.h5p.FILE_ACCESS)


def make_fcpl():
    fcpl = h5py.h5p.create(h5py.h5p.FILE_CREATE)
    flags = h5py.h5p.CRT_ORDER_TRACKED | h5py.h5p.CRT_ORDER_INDEXED
    fcpl.set_link_creation_order(flags)
    return fcpl


class File(FileMixin):

    def __init__(self, path, mode=FileMode.ReadWrite):
        try:
            path = path.encode("utf-8")
        except (UnicodeError, LookupError):
            pass
        if not os.path.exists(path):
            mode = FileMode.Overwrite

        self.mode = mode
        h5mode = map_file_mode(mode)

        if os.path.exists(path):
            self._open_existing(path, h5mode)
        else:
            self._create_new(path, h5mode)

        self._root = H5Group(self._h5file, "/", create=True)
        self._data = self._root.open_group("data", create=True)
        self.metadata = self._root.open_group("metadata", create=True)
        if "created_at" not in self._h5file.attrs:
            self.force_created_at()
        if "updated_at" not in self._h5file.attrs:
            self.force_updated_at()

    def _open_existing(self, path, h5mode):
        if h5mode == h5py.h5f.ACC_TRUNC:
            self._create_new(path, h5mode)
        else:
            fid = h5py.h5f.open(path, flags=h5mode, fapl=make_fapl())
            self._h5file = h5py.File(fid)

    def _create_new(self, path, h5mode):
        fid = h5py.h5f.create(path, flags=h5mode, fapl=make_fapl(),
                              fcpl=make_fcpl())
        self._h5file = h5py.File(fid)
        self._create_header()

    def _create_header(self):
        self.format = "nix"
        self.version = (1, 0, 0)

    @classmethod
    def open(cls, path, mode=FileMode.ReadWrite, backend=None):
        """
        Open a NIX file, or create it if it does not exist.

        :param path: Path to file
        :param mode: FileMode ReadOnly, ReadWrite, or Overwrite. Default: ReadWrite
        :param backend: Either "hdf5" or "h5py". Defaults to "hdf5" if available, or "h5py" otherwise
        :return: nixio.File object
        """
        if backend is None:
            if CFile is None:
                backend = "h5py"
            else:
                backend = "hdf5"
        if backend == "hdf5":
            if CFile:
                return CFile.open(path, mode)
            else:
                # TODO: Brief instructions or web URL for building C++ files?
                raise RuntimeError("HDF5 backend is not available.")
        elif backend == "h5py":
            return cls(path, mode)
        else:
            raise ValueError("Valid backends are 'hdf5' and 'h5py'.")

    @property
    def version(self):
        return tuple(self._h5file.attrs["version"])

    @version.setter
    def version(self, v):
        util.check_attr_type(v, tuple)
        for part in v:
            util.check_attr_type(part, int)
        self._h5file.attrs["version"] = v

    @property
    def format(self):
        return self._h5file.attrs["format"].decode()

    @format.setter
    def format(self, f):
        util.check_attr_type(f, str)
        self._h5file.attrs["format"] = f.encode("utf-8")

    @property
    def created_at(self):
        return util.str_to_time(self._h5file.attrs["created_at"])

    def force_created_at(self, t=util.now_int()):
        util.check_attr_type(t, int)
        self._h5file.attrs["created_at"] = util.time_to_str(t)

    @property
    def updated_at(self):
        return util.str_to_time(self._h5file.attrs["updated_at"])

    def force_updated_at(self, t=util.now_int()):
        util.check_attr_type(t, int)
        self._h5file.attrs["updated_at"] = util.time_to_str(t)

    def is_open(self):
        pass

    def close(self):
        self._h5file.close()

    def validate(self):
        pass

    # Block
    def create_block(self, name, type_):
        if name in self._data:
            raise ValueError("Block with the given name already exists!")
        block = Block._create_new(self._data, name, type_)
        return block

    def _get_block_by_id(self, id_or_name):
        return Block(self._data.get_by_id_or_name(id_or_name))

    def _get_block_by_pos(self, pos):
        return Block(self._data.get_by_pos(pos))

    def _delete_block_by_id(self, id_or_name):
        self._data.delete(id_or_name)

    def _block_count(self):
        return len(self._data)

    # Section
    def create_section(self, name, type_):
        if name in self.metadata:
            raise exceptions.DuplicateName("create_section")
        sec = Section._create_new(self.metadata, name, type_)
        return sec

    def _get_section_by_id(self, id_or_name):
        return Section(self.metadata.get_by_id_or_name(id_or_name))

    def _get_section_by_pos(self, pos):
        return Section(self.metadata.get_by_pos(pos))

    def _delete_section_by_id(self, id_or_name):
        self.metadata.delete(id_or_name)

    def _section_count(self):
        return len(self.metadata)

