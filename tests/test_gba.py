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
        empty = self.gbaParser.parse("data/empty")
        self.assertEqual(len(empty), 0)

        props = self.gbaParser.parse("data/Golden Sun - The Lost Age.gba")
        self.assertEqual(len(props), 8)
        self.assertEqual(props["title"], "GOLDEN_SUN_B")
        self.assertEqual(props["code"], "AGFE")
        self.assertEqual(props["publisher"], "Nintendo")
        self.assertEqual(props["publisher_code"], "01")
        self.assertEqual(props["unit_code"], "00")
        self.assertEqual(props["version"], "00")
        self.assertEqual(props["header_checksum"], "2E")
        self.assertEqual(props["platform"], "Game Boy Advance")

if __name__ == '__main__':
    unittest.main()
