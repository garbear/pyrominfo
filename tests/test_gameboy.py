#!/usr/bin/env python
#
# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

import testutils

import unittest

gameboy = testutils.loadModule("gameboy")

class TestGameboyParser(unittest.TestCase):
    def setUp(self):
        self.gbParser = gameboy.GameboyParser()

    def test_gameboy(self):
        empty = self.gbParser.parse("data/empty")
        self.assertEquals(len(empty), 0)

        props = self.gbParser.parse("data/The Legend of Zelda - Links Awakening DX.gbc")
        self.assertEquals(len(props), 15)
        self.assertEquals(props["title"], "ZELDA")
        self.assertEquals(props["platform"], "Game Boy Color")
        self.assertEquals(props["sgb_support"], "yes")
        self.assertEquals(props["publisher"], "Nintendo")
        self.assertEquals(props["publisher_code"], "01")
        self.assertEquals(props["cartridge_type"], "ROM+MBC5+RAM+BATT")
        self.assertEquals(props["cartridge_type_code"], "1B")
        self.assertEquals(props["rom_size"], "1MB")
        self.assertEquals(props["rom_size_code"], "05")
        self.assertEquals(props["ram_size"], "32KB")
        self.assertEquals(props["ram_size_code"], "03")
        self.assertEquals(props["destination"], "")
        self.assertEquals(props["version"], "00")
        self.assertEquals(props["header_checksum"], "3C")
        self.assertEquals(props["global_checksum"], "E3FD")

if __name__ == '__main__':
    unittest.main()
