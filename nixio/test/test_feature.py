# Copyright (c) 2014, German Neuroinformatics Node (G-Node)
#
# All rights reserved.
#
# Redistribution and use in section and binary forms, with or without
# modification, are permitted under the terms of the BSD License. See
# LICENSE file in the root of the Project.

from __future__ import (absolute_import, division, print_function)#, unicode_literals)

import unittest

from nixio import *
try:
    import nixio.core
    skip_cpp = False
except ImportError:
    skip_cpp = True


class _TestFeature(unittest.TestCase):

    backend = None

    def setUp(self):
        self.file     = File.open("unittest.h5", FileMode.Overwrite,
                                  backend=self.backend)
        self.block    = self.file.create_block("test block", "recordingsession")

        self.signal = self.block.create_data_array("output", "analogsignal", DataType.Float, (0, ))
        self.stimuli_tag   = self.block.create_tag(
            "stimuli used", "tag", [0]
        )
        self.stimuli_tag.references.append(self.signal)

        self.movie1 = self.block.create_data_array("stimulus movie 1", "movie", DataType.Float, (0, ))
        self.feature_1 = self.stimuli_tag.create_feature(
            self.movie1, LinkType.Tagged
        )
        self.movie2 = self.block.create_data_array("stimulus movie 2", "movie", DataType.Float, (0, ))
        self.feature_2 = self.stimuli_tag.create_feature(
            self.movie2, LinkType.Tagged
        )

    def tearDown(self):
        del self.file.blocks[self.block.id]
        self.file.close()

    def test_feature_eq(self):
        assert(self.feature_1 == self.feature_1)
        assert(not self.feature_1 == self.feature_2)
        assert(not self.feature_1 is None)

    def test_feature_id(self):
        assert(self.feature_1.id is not None)

    def test_feature_link_type(self):
        def set_none():
            self.feature_1.link_type = None

        assert(self.feature_1.link_type is not None)
        self.assertRaises(Exception, set_none)

        self.feature_1.link_type = LinkType.Untagged
        assert(self.feature_1.link_type == LinkType.Untagged)

    def test_feature_data(self):
        def set_none():
            self.feature_1.data = None

        assert(self.feature_1.data is not None)
        self.assertRaises(Exception, set_none)

        new_data_ref = self.block.create_data_array("test", "current", DataType.Float, (0, ))
        self.feature_1.data = new_data_ref
        assert(self.feature_1.data == new_data_ref)


@unittest.skipIf(skip_cpp, "HDF5 backend not available.")
class TestFeatureCPP(_TestFeature):

    backend = "hdf5"


class TestFeaturePy(_TestFeature):

    backend = "h5py"
