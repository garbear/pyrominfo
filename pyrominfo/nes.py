# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

from rominfo import RomInfoParser

class NESParser(RomInfoParser):
    """
    Parse a NES image. Valid extensions are nes, nez, unf, unif.
    NES file format documentation and related source code:
    * http://nesdev.com/neshdr20.txt
    * http://wiki.nesdev.com/w/index.php/INES
    * http://codef00.com/unif_cur.txt
    * nes.c of the MAME project:
    * http://mamedev.org/source/src/mess/machine/nes.c.html
    """

    def getValidExtensions(self):
        return ["nes", "nez", "unf", "unif"]

    def parse(self, filename):
        props = {}
        with open(filename, "rb") as f:
            ext = self._getExtension(filename)
            if ext in ["unf", "unif"]:
                data = bytearray(f.read())
            else:
                data = bytearray(f.read(16))
            if self.isValidData(data):
                props = self.parseBuffer(data)
        return props

    def isValidData(self, data):
        """
        Test for a valid NES image by checking the first 4 bytes for a UNIF or
        iNES header ("NES" followed by MS-DOS end-of-file). FDS headers
        ("FDS\x1a") are not supported, as they contain no useful information.
        """
        return data[:4] == b"NES\x1a" or data[:4] == b"UNIF"

    def parseBuffer(self, data):
        props = {}

        if data[:4] == b"NES\x1a":
            # 06 - First ROM option byte
            props["battery"] = "yes" if data[0x06] & 0x02 else ""
            props["trainer"] = "yes" if data[0x06] & 0x04 else ""
            props["four_screen_vram"] = "yes" if data[0x06] & 0x08 else ""

            # 07 - Second ROM option byte
            ines2 = (data[0x07] & 0x0c == 0x8)
            props["header"] = "iNES 2.0" if ines2 else "iNES"

            # 0C - iNES 2.0 headers can specify TV system. If the second bit is set
            #      (data[0x0c] & 0x2) then the ROM works with both PAL and NTSC machines.
            #
            # iNES 1.0 doesn't store video information. FCEU-Next compensates by matching
            # the following PAL country tags in filenames:
            #     (E), (F), (G), (I), (Europe), (Australia), (France), (Germany),
            #     (Sweden), (En, Fr, De), (Italy)
            # See https://github.com/libretro/fceu-next/blob/master/src-fceux/ines.cpp
            props["video_output"] = ("PAL" if data[0x0c] & 0x1 else "NTSC") if ines2 else ""

            props["title"] = ""

        elif data[:4] == b"UNIF":
            props["header"] = "UNIF"

            # Set defaults to be overridden in our chunked reads later
            props["battery"] = ""
            props["trainer"] = ""
            props["four_screen_vram"] = ""
            props["video_output"] = ""
            props["title"] = ""

            # Skip the UNIF header (0x20 / 32 bytes) and continue with chunked reads
            data = data[0x20 : ]
            while len(data) > 8:
                size = 0
                sizestr = data[4:8]
                if len(sizestr) == 4:
                    size = sizestr[0] | (sizestr[1] << 8) | (sizestr[2] << 16) | (sizestr[3] << 24)
                if size == 0:
                    continue

                ID = self._sanitize(data[ : 4])
                chunk = data[8 : 8 + size]
                data = data[8 + size : ] # Fast-forward past chunk's data

                if ID == "NAME":
                    props["title"] = self._sanitize(chunk)
                elif ID == "TVCI":
                    props["video_output"] = "NTSC" if chunk[0] == 0x00 else "PAL" if chunk[0] == 0x01 else ""
                elif ID == "BATR":
                    props["battery"] = "yes"
                elif ID == "MIRR":
                    if chunk[0] == 0x04:
                        props["four_screen_vram"] = "yes"

        return props

RomInfoParser.registerParser(NESParser())
