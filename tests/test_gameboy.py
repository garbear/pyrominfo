# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

import testutils

import unittest

gameboy = testutils.loadModule("gameboy")

class TestGameboyParser(unittest.TestCase):
    def setUp(self):
        self.gbParser = gameboy.GameboyParser()

    def test_gameboy(self):
        invalid = self.gbParser.parseGameboy("data/invalid")
        self.assertEquals(len(invalid), 0)

        empty = self.gbParser.parseGameboy("data/empty")
        self.assertEquals(len(empty), 0)

        props = self.gbParser.parseGameboy("data/Tetris.gb")
        self.assertEquals(len(props), 4)
        self.assertEquals(props["code"], "TETRIS")
        self.assertEquals(props["publisher"], "Nintendo")
        self.assertEquals(props["publisher_code"], "01")
        self.assertEquals(props["platform"], "Game Boy")

    def test_gameboy_advance(self):
        invalid = self.gbParser.parseGameboy("data/invalid")
        self.assertEquals(len(invalid), 0)

        empty = self.gbParser.parseGameboyAdvance("data/empty")
        self.assertEquals(len(empty), 0)

        props = self.gbParser.parseGameboyAdvance("data/Disney Princess - Royal Adventure.gba")
        self.assertEquals(len(props), 5)
        self.assertEquals(props["title"], "PRINCESSTOWN")
        self.assertEquals(props["code"], "BQNP")
        self.assertEquals(props["publisher"], "Disney")
        self.assertEquals(props["publisher_code"], "4Q")
        self.assertEquals(props["platform"], "Game Boy Advance")

if __name__ == '__main__':
    unittest.main()
