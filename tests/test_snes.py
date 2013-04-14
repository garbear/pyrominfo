#!/usr/bin/env python
#
# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

import testutils

import unittest

snes = testutils.loadModule("snes")

class TestSNESParser(unittest.TestCase):
    def setUp(self):
        self.snesParser = snes.SNESParser()

    def test_gba(self):
        invalid = self.snesParser.parse("data/invalid")
        self.assertEquals(len(invalid), 0)

        empty = self.snesParser.parse("data/empty")
        self.assertEquals(len(empty), 0)

        props = self.snesParser.parse("data/Super Mario World.smc")
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
