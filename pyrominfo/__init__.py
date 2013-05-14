# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

from rominfo import RomInfoParser

__all__ = [
    "RomInfo",
    "gameboy",
    "gba",
    "genesis",
    "mastersystem",
    "nes",
    "nintendo64",
    "snes",
]

class RomInfo(object):
    @staticmethod
    def parse(filename):
        ext = None
        for parser in RomInfoParser.getParsers():
            if not ext:
                ext = parser._getExtension(filename)
            if parser.isValidExtension(ext):
                props = parser.parse(filename)
                if props and any(props):
                    return props
        return {}

    @staticmethod
    def parseBuffer(data):
        for parser in RomInfoParser.getParsers():
            if parser.isValidData(data):
                props = parser.parseBuffer(data)
                if props and any(props):
                    return props
        return {}
