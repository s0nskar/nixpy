# Copyright (c) 2014, German Neuroinformatics Node (G-Node)
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted under the terms of the BSD License. See
# LICENSE file in the root of the Project.
from __future__ import (absolute_import, division, print_function)

import unittest
import numpy as np

from nixio import *
try:
    import nixio.core
    skip = False
except ImportError:
    skip = True


@unittest.skipIf(skip, "HDF5 backend not available.")
class _TestBackendCompatibility(unittest.TestCase):

    def setUp(self):
        self.write_file = File.open("compat_test.h5", FileMode.Overwrite,
                                    backend=self.write_backend)
        self.read_file = None

    def tearDown(self):
        self.write_file.close()
        if self.read_file:
            self.read_file.close()

    def check_containers(self, cont_one, cont_two):
        self.assertEqual(len(cont_one), len(cont_two))
        for idx in range(len(cont_one)):
            item_one = cont_one[idx]
            item_two = cont_two[idx]
            self.assertEqual(item_one.id, item_two.id)
            if len(item_one.sources) or len(item_two.sources):
                self.check_containers(item_one.sources, item_two.sources)

    def check_compatibility(self):
        self.read_file = File.open("compat_test.h5", FileMode.ReadOnly,
                                   backend=self.read_backend)

        self.check_containers(self.write_file.blocks, self.read_file.blocks)

        for blkidx in range(len(self.write_file.blocks)):
            wblock = self.write_file.blocks[blkidx]
            rblock = self.read_file.blocks[blkidx]
            self.check_containers(wblock.groups, rblock.groups)
            self.check_containers(wblock.data_arrays, rblock.data_arrays)
            self.check_containers(wblock.tags, rblock.tags)
            self.check_containers(wblock.multi_tags, rblock.multi_tags)
            for grpidx in range(len(wblock.groups)):
                wgrp = wblock.groups[grpidx]
                rgrp = rblock.groups[grpidx]
                self.check_containers(wgrp.data_arrays, rgrp.data_arrays)
                self.check_containers(wgrp.tags, rgrp.tags)
                self.check_containers(wgrp.multi_tags, rgrp.multi_tags)

    def test_blocks(self):
        for idx in range(10):
            self.write_file.create_block("test_block" + str(idx),
                                         "blocktype")

        self.check_compatibility()

    def test_groups(self):
        blk = self.write_file.create_block("test_block", "blocktype")
        for idx in range(12):
            blk.create_group("group_" + str(idx), "grouptype")

        self.check_compatibility()

    def test_data_arrays(self):
        blk = self.write_file.create_block("testblock", "blocktype")
        grp = blk.create_group("testgroup", "grouptype")

        for idx in range(7):
            da = blk.create_data_array("data_" + str(idx), "thedata",
                                       data=np.random.random(40))
            if (idx % 2) == 0:
                grp.data_arrays.append(da)

        self.check_compatibility()
        wdata = blk.data_arrays
        rdata = self.read_file.blocks[0].data_arrays
        for wda, rda in zip(wdata, rdata):
            np.testing.assert_almost_equal(wda[:], rda[:])

    def test_tags(self):
        blk = self.write_file.create_block("testblock", "blocktype")
        grp = blk.create_group("testgroup", "grouptype")

        for idx in range(7):
            tag = blk.create_tag("tag_" + str(idx), "atag",
                                 np.random.random(idx*2))
            tag.extent = np.random.random(idx*2)
            if (idx % 3) == 0:
                grp.tags.append(tag)

        self.check_compatibility()
        wtags = blk.tags
        rtags = self.read_file.blocks[0].tags
        for wtag, rtag in zip(rtags, wtags):
            np.testing.assert_almost_equal(wtag.position, rtag.position)
            np.testing.assert_almost_equal(wtag.extent, rtag.extent)

    def test_multi_tags(self):
        blk = self.write_file.create_block("testblock", "blocktype")
        grp = blk.create_group("testgroup", "grouptype")

        for idx in range(11):
            posda = blk.create_data_array("pos_" + str(idx), "positions",
                                          data=np.random.random(idx*10))
            extda = blk.create_data_array("ext_" + str(idx), "extents",
                                          data=np.random.random(idx*10))
            mtag = blk.create_multi_tag("mtag_" + str(idx), "some multi tag",
                                        posda)
            mtag.extents = extda

            if (idx % 2) == 0:
                grp.multi_tags.append(mtag)

        self.check_compatibility()
        wmts = blk.multi_tags
        rmts = self.read_file.blocks[0].multi_tags
        for wmt, rmt in zip(wmts, rmts):
            np.testing.assert_almost_equal(wmt.positions[:], rmt.positions[:])
            np.testing.assert_almost_equal(wmt.extents[:], rmt.extents[:])

    def test_sources(self):
        blk = self.write_file.create_block("testblock", "sourcetest")
        grp = blk.create_group("testgroup", "sourcetest")
        da = blk.create_data_array("da", "sourcetest",
                                   data=np.random.random(10))
        pos = blk.create_data_array("pos", "sourcetest",
                                    data=np.random.random(10))
        mtag = blk.create_multi_tag("mtag", "sourcetest", pos)
        grp.data_arrays.append(da)

        for idx in range(20):
            src = blk.create_source("src" + str(idx), "source")

            if (idx % 5) == 0:
                grp.sources.append(src)

            if (idx % 3) == 0:
                mtag.sources.append(src)

            if (idx % 8) == 0:
                da.sources.append(src)

        self.check_compatibility()

    def test_dimensions(self):
        blk = self.write_file.create_block("testblock", "dimtest")

        da_set = blk.create_data_array("da with seet", "datype",
                                       data=np.random.random(20))
        da_set.append_set_dimension()
        da_set.dimensions[0].labels = ["label one", "label two"]

        da_range = blk.create_data_array("da with range", "datype",
                                         data=np.random.random(12))
        da_range.append_range_dimension(np.random.random(12))
        da_range.dimensions[0].label = "range dim label"

        da_sample = blk.create_data_array("da with sample", "datype",
                                          data=np.random.random(10))
        da_sample.append_sampled_dimension(0.3)
        da_sample.dimensions[0].label = "sample dim label"

        self.check_compatibility()

        for idx in range(len(blk.data_arrays)):
            wda = self.write_file.blocks[0].data_arrays[idx]
            rda = self.read_file.blocks[0].data_arrays[idx]
            wdadim = wda.dimensions[0]
            rdadim = rda.dimensions[0]

            self.assertEqual(wdadim.dimension_type,
                             rdadim.dimension_type)

            if hasattr(wdadim, "label"):
                self.assertEqual(wdadim.label, rdadim.label)
            else:
                self.assertEqual(wdadim.labels, rdadim.labels)


class TestWriteCPPReadPy(_TestBackendCompatibility):

    write_backend = "hdf5"
    read_backend = "h5py"


class TestWritePyReadCPP(_TestBackendCompatibility):

    write_backend = "h5py"
    read_backend = "hdf5"