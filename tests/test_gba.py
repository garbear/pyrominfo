#!/usr/bin/env python
#
# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

import testutils

import unittest

gba = testutils.loadModule("gba")

class TestGBAParser(unittest.TestCase):
    def setUp(self):
        self.gbaParser = gba.GBAParser()

    def test_gba(self):
        invalid = self.gbaParser.parse("data/invalid")
        self.assertEquals(len(invalid), 0)

        empty = self.gbaParser.parse("data/empty")
        self.assertEquals(len(empty), 0)

        props = self.gbaParser.parse("data/Golden Sun - The Lost Age.gba")
        self.assertEquals(len(props), 8)
        self.assertEquals(props["title"], "GOLDEN_SUN_B")
        self.assertEquals(props["code"], "AGFE")
        self.assertEquals(props["publisher"], "Nintendo")
        self.assertEquals(props["publisher_code"], "01")
        self.assertEquals(props["unit_code"], "00")
        self.assertEquals(props["version"], "00")
        self.assertEquals(props["header_checksum"], "2E")
        self.assertEquals(props["platform"], "Game Boy Advance")

if __name__ == '__main__':
    unittest.main()
