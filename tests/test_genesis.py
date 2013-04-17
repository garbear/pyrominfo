#!/usr/bin/env python
#
# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

import testutils

import unittest

genesis = testutils.loadModule("genesis")

class TestGenesisParser(unittest.TestCase):
    def setUp(self):
        self.genesisParser = genesis.GensisParser()

    def test_genesis(self):
        empty = self.genesisParser.parse("data/empty")
        self.assertEquals(len(empty), 0)

        props = self.genesisParser.parse("data/Sonic the Hedgehog.bin")
        print "%s" % props
        self.assertEquals(len(props), 13)
        self.assertEquals(props["console"], "SEGA MEGA DRIVE")
        self.assertEquals(props["copyright"], "(C)SEGA 1991.APR")
        self.assertEquals(props["publisher"], "SEGA")
        self.assertEquals(props["foreign_title"], "SONIC THE               HEDGEHOG")
        self.assertEquals(props["title"], "SONIC THE               HEDGEHOG")
        self.assertEquals(props["classification"], "Game")
        self.assertEquals(props["code"], "00001009")
        self.assertEquals(props["version"], "00")
        self.assertEquals(props["checksum"], "264A")
        self.assertEquals(props["device_codes"], "J")
        self.assertEquals(props["devices"], "3B Joypad")
        self.assertEquals(props["memo"], "")
        self.assertEquals(props["country_codes"], "JUE")

if __name__ == '__main__':
    unittest.main()
