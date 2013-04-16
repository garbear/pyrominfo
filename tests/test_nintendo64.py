#!/usr/bin/env python
#
# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

import testutils

import unittest

nintendo64 = testutils.loadModule("nintendo64")

class TestNintendo64Parser(unittest.TestCase):
    def setUp(self):
        self.n64Parser = nintendo64.Nintendo64Parser()

    def test_nintendo64(self):
        empty = self.n64Parser.parse("data/empty")
        self.assertEquals(len(empty), 0)

        props = self.n64Parser.parse("data/Super Smash Bros.z64")
        print "%s" % props
        self.assertEquals(len(props), 11)
        self.assertEquals(props["title"], "SMASH BROTHERS")
        self.assertEquals(props["clock_rate"], "SMASH BROTHERS")
        self.assertEquals(props["version"], "SMASH BROTHERS")
        self.assertEquals(props["crc1"], "SMASH BROTHERS")
        self.assertEquals(props["crc2"], "SMASH BROTHERS")
        self.assertEquals(props["publisher"], "Nintendo")
        self.assertEquals(props["publisher_code"], "N")
        self.assertEquals(props["code"], "AL")
        self.assertEquals(props["region"], "USA")
        self.assertEquals(props["region_code"], "45")
        self.assertEquals(props["image_format"], "45")

if __name__ == '__main__':
    unittest.main()
