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
        self.assertEqual(len(empty), 0)

        props = self.n64Parser.parse("data/Super Smash Bros.z64")
        self.assertEqual(len(props), 9)
        self.assertEqual(props["title"], "SMASH BROTHERS")
        self.assertEqual(props["version"], "00001449")
        self.assertEqual(props["crc1"], "916B8B5B")
        self.assertEqual(props["crc2"], "780B85A4")
        self.assertEqual(props["publisher"], "Nintendo")
        self.assertEqual(props["publisher_code"], "N")
        self.assertEqual(props["code"], "AL")
        self.assertEqual(props["region"], "USA")
        self.assertEqual(props["region_code"], "45")

if __name__ == '__main__':
    unittest.main()
