#!/usr/bin/env python
#
# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

import testutils

import unittest

nes = testutils.loadModule("nes")

class TestNESParser(unittest.TestCase):
    def setUp(self):
        self.nesParser = nes.NESParser()

    def test_gameboy(self):
        empty = self.nesParser.parse("data/empty")
        self.assertEquals(len(empty), 0)

        props = self.nesParser.parse("data/Dancing Blocks (1990)(Sachen)(AS)[p][!][SA-013][NES cart].unf")
        self.assertEquals(len(props), 6)
        self.assertEquals(props["battery"], "")
        self.assertEquals(props["trainer"], "")
        self.assertEquals(props["four_screen_vram"], "")
        self.assertEquals(props["header"], "UNIF")
        self.assertEquals(props["video_output"], "")
        self.assertEquals(props["title"], "Dancing Blocks (72 pin cart)")

if __name__ == '__main__':
    unittest.main()
