# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

from rominfo import RomInfoParser

# Publishers are the same across these handhelds
from gameboy import gameboy_publishers

class GBAParser(RomInfoParser):
    """
    Parse a Nintendo Gameboy Advance image. Valid extensions are gba, agb.
    Gameboy Advance header references and related source code:
    * http://z9.invisionfree.com/Golden_Sun_Hacking/index.php?showtopic=241
    * http://members.iinet.net.au/~freeaxs/gbacomp (Nintendo Logo data)
    * RomInfo.cpp of the VBA-M project:
    * http://vbam.svn.sourceforge.net/viewvc/vbam/trunk/src/win32/RomInfo.cpp?view=markup
    """

    def getValidExtensions(self):
        return ["gba", "agb"]

    def parse(self, filename):
        props = {}
        with open(filename, "rb") as f:
            data = bytearray(f.read(0xc0))
            if self.isValidData(data):
                props = self.parseBuffer(data)
        return props

    def isValidData(self, data):
        """
        The watermark we use here is the Nintendo logo. The Nintendo logo that is
        displayed when the Gameboy gets turned on is stored in the 156 bytes from
        address $0004 to $009F. See the comment in gameboy.py for more info.
        """
        nintendo_logo = [
            # GBA is ARM microprocessor, so first 4 bytes is 32-bit ARM opcode saying "jump elsewhere"
                                    0x24, 0xFF, 0xAE, 0x51, 0x69, 0x9A, 0xA2, 0x21, 0x3D, 0x84, 0x82, 0x0A,
            0x84, 0xE4, 0x09, 0xAD, 0x11, 0x24, 0x8B, 0x98, 0xC0, 0x81, 0x7F, 0x21, 0xA3, 0x52, 0xBE, 0x19,
            0x93, 0x09, 0xCE, 0x20, 0x10, 0x46, 0x4A, 0x4A, 0xF8, 0x27, 0x31, 0xEC, 0x58, 0xC7, 0xE8, 0x33,
            0x82, 0xE3, 0xCE, 0xBF, 0x85, 0xF4, 0xDF, 0x94, 0xCE, 0x4B, 0x09, 0xC1, 0x94, 0x56, 0x8A, 0xC0,
            0x13, 0x72, 0xA7, 0xFC, 0x9F, 0x84, 0x4D, 0x73, 0xA3, 0xCA, 0x9A, 0x61, 0x58, 0x97, 0xA3, 0x27,
            0xFC, 0x03, 0x98, 0x76, 0x23, 0x1D, 0xC7, 0x61, 0x03, 0x04, 0xAE, 0x56, 0xBF, 0x38, 0x84, 0x00,
            0x40, 0xA7, 0x0E, 0xFD, 0xFF, 0x52, 0xFE, 0x03, 0x6F, 0x95, 0x30, 0xF1, 0x97, 0xFB, 0xC0, 0x85,
            0x60, 0xD6, 0x80, 0x25, 0xA9, 0x63, 0xBE, 0x03, 0x01, 0x4E, 0x38, 0xE2, 0xF9, 0xA2, 0x34, 0xFF,
            0xBB, 0x3E, 0x03, 0x44, 0x78, 0x00, 0x90, 0xCB, 0x88, 0x11, 0x3A, 0x94, 0x65, 0xC0, 0x7C, 0x63,
            0x87, 0xF0, 0x3C, 0xAF, 0xD6, 0x25, 0xE4, 0x8B, 0x38, 0x0A, 0xAC, 0x72, 0x21, 0xD4, 0xF8, 0x07,
        ]
        return [b for b in data[0x04 : 0x04 + len(nintendo_logo)]] == nintendo_logo

    def parseBuffer(self, data):
        props = {}

        # 00A0-00AB - Title, UPPER CASE ASCII, padded with 00h (if less than 12 chars)
        props["title"] = self._sanitize(data[0xa0 : 0xa0 + 12])

        # 00AC-00AF - Code, UPPER CASE ASCII
        # This is the same code as the AGB-UTTD code which is printed on the package
        # and sticker on (commercial) cartridges (excluding the leading "AGB-" part).
        # See http://z9.invisionfree.com/Golden_Sun_Hacking/index.php?showtopic=241
        # for the breakdown of what values U, TT and D can have.
        props["code"] = self._sanitize(data[0xac : 0xac + 4])

        # 00B0-00B1 - Licensee, UPPER CASE ASCII
        pub = data[0xb0 : 0xb0 + 2].decode("ascii", "ignore")
        props["publisher"] = gameboy_publishers.get(pub, "")
        props["publisher_code"] = pub

        # 00B3 - Main unit code, identifies the required hardware (00h for current GBA models)
        props["unit_code"] = "%02X" % data[0xb3]

        # 00BC - Software version of the game, usually zero
        props["version"] = "%02X" % data[0xbc]

        # 00BD - Header checksum, 8 bit checksum across the cartridge header bytes 00A0-00BC
        props["header_checksum"] = "%02X" % data[0xbd]

        props["platform"] = "Game Boy Advance"

        return props

RomInfoParser.registerParser(GBAParser())
