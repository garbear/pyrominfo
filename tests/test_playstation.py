#!/usr/bin/env python
#
# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

import testutils

import unittest

ps = testutils.loadModule("playstation")

class TestGenesisParser(unittest.TestCase):
    def setUp(self):
        self.psParser = ps.PlayStationParser()

    def test_genesis(self):
        empty = self.psParser.parse("data/empty")
        self.assertEquals(len(empty), 0)

        #props = self.psParser.parse("data/metal_gear_solid_(v1.1)_(disc_1).iso")
        #props = self.psParser.parse("data/iso-dirtree1.iso")
        props = self.psParser.parse("data/mini_x64.iso")
        #print "props: %s" % props
        #self.assertEquals(len(props), 2)
        #self.assertEquals(props["license_line1"], "Licensed  by")
        #self.assertEquals(props["license_line2"], "Sony Computer Entertainment Amer")

if __name__ == '__main__':
    unittest.main()
