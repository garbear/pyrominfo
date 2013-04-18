# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

from rominfo import RomInfoParser

class GensisParser(RomInfoParser):
    """
    Parse a Sega Gensis image. Valid extensions are sms, smd, md, bin, gg, sg, mdx.
    Sega Gensis header references and related source code:
    * http://www.zophar.net/fileuploads/2/10614uauyw/Genesis_ROM_Format.txt
    * http://en.wikibooks.org/wiki/Genesis_Programming
    * http://www.smspower.org/Development/ROMHeader
    * loadrom.c of the Genesis Plus GX project:
    * https://code.google.com/p/genplus-gx/source/browse/trunk/source/loadrom.c
    """

    def getValidExtensions(self):
        return ["sms", "smd", "md", "bin", "gg", "sg", "mdx"] # TODO: Implement others

    def parse(self, filename):
        props = {}
        with open(filename, "rb") as f:
            data = bytearray(f.read())
            if len(data):
                props = self.parseBuffer(data) 
        return props

    def isValidData(self, data):
        """
        This is just the console name (depending on the console's country of origin).
        """
        return data[0x100 : 0x100 + 15] == b"SEGA MEGA DRIVE" or \
               data[0x100 : 0x100 + 12] == b"SEGA GENESIS"

    def parseBuffer(self, data):
        props = {}

        # Auto-detect 512 byte extra header
        size = len(data)
        if data[0x100 : 0x100 + 4] != b"SEGA" and (size >> 9) & 1 != 0 and size % 512 == 0:
            data = data[0x200 : ]

            # TODO: assume/detect interleaved Genesis ROM format (.smd) and de-interleave

        # Sniff out Master System ROM header.
        # Gensis Plus GX looks at addresses 0x1FF0, 0x3FF0, 0x7FF0.
        # Quite a few ROMs, including "Strider (UE) [!].sms", use address 0x81F0.
        # X-MAME 0.106 has code to check this address, but the code is commented out...
        # https://code.oregonstate.edu/svn/dsp_bd/uclinux-dist/trunk/user/games/xmame/xmame-0.106/mess/machine/sms.c
        offset = 0
        if len(data) > 0x8000:
            for off in [0x1ff0, 0x3ff0, 0x7ff0, 0x81f0]:
                if data[off : off + 8] == b"TMR SEGA":
                    offset = off
                    break
        if offset:
            # Found a Master System ROM header, assuming header starts at address 7ff0
            data = data[offset : ]

            # 7FF0-7FF7 - Magic word "TMR SEGA"
            # 7FF8-7FF9 - Reserved space
            # 7FFA-7FFB - Checksum, little endian
            props["checksum"] = "%04X" % ((data[0x0a] << 8) | data[0x0b])

            # 7FFC-7FFE.8 - Product code. The first 2 bytes are a Binary Coded Decimal
            #               representation of the last four digits of the product code.
            #               The high 4 bits of the next byte are a hexadecimal representation
            #               of any remaining digits of the product code.
            props["code"] = "%02d%02X%02X" % (data[0x0e] >> 4, data[0x0d], data[0x0c])

            # 7FFE.8 - Version. The low 4 bits give a version number
            props["version"] = "%02X" % (data[0x0e] & 0x0f)

            # 7FFF.8 - Region and system for which the cartridge is intended
            r = (data[0x0f] >> 4)
            props["console"] = "Sega Master System" if r in [3, 4] else "Game Gear" if r in [5, 6, 7] else ""
            props["region"] = "Japan" if r in [3, 5] else "Export" if r in [4, 6] else "International" if r == 7 else ""

            # 7FFF.8 - ROM size. Final 4 bits give the ROM size, some values are buggy. Not implemented.

            # TODO
            props["copyright"] = ""
            props["publisher"] = ""
            props["foreign_title"] = ""
            props["title"] = ""
            props["classification"] = ""
            props["device_codes"] = ""
            props["devices"] = ""
            props["memo"] = ""
            props["country_codes"] = ""

        else:
            # 0100-010f - Console name, can be "SEGA MEGA DRIVE" or "SEGA GENESIS"
            #             depending on the console's country of origin.
            props["console"] = self._sanitize(data[0x100 : 0x100 + 16])

            # 0110-011f - Copyright notice, in most cases of this format: (C)T-XX 1988.JUL
            props["copyright"] = self._sanitize(data[0x110 : 0x110 + 16])

            # Publisher data is extracted from copyright notice
            props["publisher"] = self.getPublisher(props["copyright"])

            # 0120-014f - Domestic name, the name the game has in its country of origin
            props["foreign_title"] = self._sanitize(data[0x120 : 0x120 + 48])

            # 0150-017f - International name, the name the game has worldwide
            props["title"] = self._sanitize(data[0x150 : 0x150 + 48])

            # 0180-0181 - Type of product. Known values: GM = Game,  AL = Education
            #             en.wikibooks.org uses AL, Genesis_ROM_Format.txt Uses Al, loadrom.c uses AI...
            props["classification"] = "Game" if data[0x180 : 0x180 + 2] == b"GM" else ("Education (%s)" % data[0x180 : 0x180 + 2])

            # 0183-018A - Product code (type was followed by a space)
            props["code"] = self._sanitize(data[0x183 : 0x183 + 8])

            # 018C-018D - Product version (code was followed by a hyphen "-")
            props["version"] = self._sanitize(data[0x18c : 0x18c + 2])

            # 018E-018F - Checksum
            props["checksum"] = "%04X" % ((data[0x18e] << 8) | data[0x18f])

            # 0190-019F - I/O device support
            props["device_codes"] = self._sanitize(data[0x190 : 0x190 + 16])
            props["devices"] = ", ".join([genesis_devices.get(d) for d in props["device_codes"] \
                                                                 if d in genesis_devices])

            # 01C8-01EF - Memo
            props["memo"] = self._sanitize(data[0x1c8 : 0x1c8 + 40])

            # 01F0-01FF - Countries in which the product can be released. This field
            #             can contain up to three countries.
            props["country_codes"] = self._sanitize(data[0x1f0 : 0x1f0 + 16])
            props["region"] = ""

        return props

    def getPublisher(self, copyright_str):
        """
        Resolve a copyright string into a publisher name. It SHOULD be 4
        characters after a (C) symbol, but there are variations. When the
        company uses a number as a company code, the copyright usually has
        this format: '(C)T-XX 1988.JUL', where XX is the company code.
        """
        company = copyright_str[3:7]
        if "-" in company:
            company = company[company.rindex("-") + 1 : ]
        company = company.rstrip()
        return gensis_publishers.get(company, "")

RomInfoParser.registerParser(GensisParser())


genesis_devices = {
    "J": "3B Joypad",
    "6": "6B Joypad",
    "K": "Keyboard",
    "P": "Printer",
    "B": "Control Ball",
    "F": "Floppy Drive",
    "L": "Activator",
    "4": "Team Player",
    "0": "MS Joypad",
    "R": "RS232C Serial",
    "T": "Tablet",
    "V": "Paddle",
    "C": "CD-ROM",
    "M": "Mega Mouse",
    "G": "Menacer",
}

gensis_publishers = {
    "ACLD": "Ballistic",
    "RSI":  "Razorsoft",
    "SEGA": "SEGA",
    "TREC": "Treco",
    "VRGN": "Virgin Games",
    "WSTN": "Westone",
    "10":   "Takara",
    "11":   "Taito or Accolade",
    "12":   "Capcom",
    "13":   "Data East",
    "14":   "Namco or Tengen",
    "15":   "Sunsoft",
    "16":   "Bandai",
    "17":   "Dempa",
    "18":   "Technosoft",
    "19":   "Technosoft",
    "20":   "Asmik",
    "22":   "Micronet",
    "23":   "Vic Tokai",
    "24":   "American Sammy",
    "29":   "Kyugo",
    "32":   "Wolfteam",
    "33":   "Kaneko",
    "35":   "Toaplan",
    "36":   "Tecmo",
    "40":   "Toaplan",
    "42":   "UFL Company Limited",
    "43":   "Human",
    "45":   "Game Arts",
    "47":   "Sage's Creation",
    "48":   "Tengen",
    "49":   "Renovation or Telenet",
    "50":   "Electronic Arts",
    "56":   "Razorsoft",
    "58":   "Mentrix",
    "60":   "Victor Musical Ind.",
    "69":   "Arena",
    "70":   "Virgin",
    "73":   "Soft Vision",
    "74":   "Palsoft",
    "76":   "Koei",
    "79":   "U.S. Gold",
    "81":   "Acclaim/Flying Edge",
    "83":   "Gametek",
    "86":   "Absolute",
    "87":   "Mindscape",
    "93":   "Sony",
    "95":   "Konami",
    "97":   "Tradewest",
    "100":  "T*HQ Software",
    "101":  "Tecmagik",
    "112":  "Designer Software",
    "113":  "Psygnosis",
    "119":  "Accolade",
    "120":  "Code Masters",
    "125":  "Interplay",
    "130":  "Activision",
    "132":  "Shiny & Playmates",
    "144":  "Atlus",
    "151":  "Infogrames",
    "161":  "Fox Interactive",
    "177":  "Ubisoft",
    "239":  "Disney Interactive",
}
