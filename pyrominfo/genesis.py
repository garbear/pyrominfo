# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

from rominfo import RomInfoParser

class GensisParser(RomInfoParser):
    """
    Parse a Sega Gensis image. Valid extensions are sms, smd, md, bin, gg, sg, mdx.
    Sega Gensis header references and related source code:
    * http://www.zophar.net/fileuploads/2/10614uauyw/Genesis_ROM_Format.txt
    * http://en.wikibooks.org/wiki/Genesis_Programming
    """

    def getValidExtensions(self):
        return ["sms", "smd", "md", "bin", "gg", "sg", "mdx"]

    def parse(self, filename):
        props = {}
        with open(filename, "rb") as f:
            data = bytearray(f.read())
            if self.isValidData(data):
                props = self.parseBuffer(data) 
        return props

    def isValidData(self, data):
        """
        This is just the console name (depending on the console's country of origin).
        TODO: Just test for the name SEGA?
        """
        return data[0x100 : 0x100 + 15] == b"SEGA MEGA DRIVE" or \
               data[0x100 : 0x100 + 12] == b"SEGA GENESIS"

    def parseBuffer(self, data):
        props = {}

        # Auto-detect 512 byte extra header
        size = len(data)
        if data[0x100 : 0x100 + 4] != b"SEGA" and (size >> 9) & 1 != 0 and size % 512 == 0:
            data = data[0x200 : ]

            # TODO: assume interleaved Genesis ROM format (.smd) and de-interleave

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

        return props

    def getPublisher(self, copyright):
        """
        Resolve a copyright string into a publisher name. It SHOULD be 4
        characters after a (C) symbol, but there are variations. When the
        company uses a number as a company code, the copyright usually has
        this format: '(C)T-XX 1988.JUL', where XX is the company code.
        """
        company = copyright[3:7]
        if "-" in company:
            company = company[company.rindex("-") + 1 : ]
        company = company.rstrip()
        return gensis_publishers.get(company, "")

RomInfoParser.registerParser(GensisParser())


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
