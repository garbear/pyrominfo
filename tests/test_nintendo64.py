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
        invalid = self.n64Parser.parse("data/invalid")
        self.assertEquals(len(invalid), 0)

        empty = self.n64Parser.parse("data/empty")
        self.assertEquals(len(empty), 0)

        props = self.n64Parser.parse("data/Super Smash Bros.z64")
        self.assertEquals(len(props), 5)
        self.assertEquals(props["title"], "SMASH BROTHERS")
        self.assertEquals(props["code"], "AL")
        self.assertEquals(props["publisher"], "Nintendo")
        self.assertEquals(props["region"], "USA")
        self.assertEquals(props["region_code"], "45")

if __name__ == '__main__':
    unittest.main()
