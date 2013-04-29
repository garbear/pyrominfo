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

    def test_snes(self):
        empty = self.snesParser.parse("data/empty")
        self.assertEquals(len(empty), 0)

        #props = self.snesParser.parse("data/Super Mario World.smc")
        #self.assertEquals(len(props), 14)
        #self.assertEquals(props["title"], "SUPER MARIOWORLD")
        #self.assertEquals(props["code"], "")
        #self.assertEquals(props["memory_layout"], "LoROM")
        #self.assertEquals(props["rom_speed"], "SlowROM")
        #self.assertEquals(props["cartridge_type"], "ROM+RAM+BATT")
        #self.assertEquals(props["rom_size"], "4 Mbit")
        #self.assertEquals(props["ram_size"], "16 Kbit")
        #self.assertEquals(props["region"], "USA/Canada")
        #self.assertEquals(props["video_output"], "NTSC")
        #self.assertEquals(props["publisher"], "Nintendo")
        #self.assertEquals(props["publisher_code"], "0001")
        #self.assertEquals(props["version"], "00")
        #self.assertEquals(props["checksum"], "A0DA")
        #self.assertEquals(props["checksum_complement"], "5F25")

        props = self.snesParser.parse("data/Power Drive (U) (Beta) (M5).smc")
        self.assertEquals(len(props), 14)
        self.assertEquals(props["title"], "POWERDRIVE")
        self.assertEquals(props["code"], "")
        self.assertEquals(props["memory_layout"], "LoROM")
        self.assertEquals(props["rom_speed"], "FastROM")
        self.assertEquals(props["cartridge_type"], "ROM")
        self.assertEquals(props["rom_size"], "8 Mbit")
        self.assertEquals(props["ram_size"], "8 Kbit")
        self.assertEquals(props["region"], "")
        self.assertEquals(props["video_output"], "")
        self.assertEquals(props["publisher"], "")
        self.assertEquals(props["publisher_code"], "0001")
        self.assertEquals(props["version"], "00")
        self.assertEquals(props["checksum"], "0000")
        self.assertEquals(props["checksum_complement"], "FFFF")


if __name__ == '__main__':
    unittest.main()
