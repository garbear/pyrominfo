# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

from rominfo import RomInfoParser

class Nintendo64Parser(RomInfoParser):
    """
    Parse a Nintendo 64 image. Valid extensions are z64 (native byte order),
    n64 (wordswapped), and v64 (byteswapped). Nintendo 64 header references and
    related source code:
    * See rom.c of the Mupen64Plus project:
    * https://bitbucket.org/richard42/mupen64plus-core/src/4cd70c2b5d38/src/main/rom.c
    """

    def getValidExtensions(self):
        return ["n64", "v64", "z64"]

    def parse(self, filename):
        props = {}
        try:
            data = open(filename, "rb").read(64)
            if self.isValidData(data):
                props = self.parseBuffer(data)
        except IOError:
            pass
        return props

    def isValidData(self, data):
        """
        Test for a valid N64 image by checking the first 4 bytes for the magic word.
        """
        if len(data) >= 64:
            # Test if rom is a native .z64 image with header 0x80371240. [ABCD]
            if [ord(b) for b in data[:4]] == [0x80, 0x37, 0x12, 0x40]:
                return True
            # Test if rom is a byteswapped .v64 image with header 0x37804012. [BADC]
            if [ord(b) for b in data[:4]] == [0x37, 0x80, 0x40, 0x12]:
                return False # TODO: Add byte-swapping
            # Test if rom is a wordswapped .n64 image with header  0x40123780. [DCBA]
            if [ord(b) for b in data[:4]] == [0x40, 0x12, 0x37, 0x80]:
                return False # TODO: Add word-swapping
        return False

    def parseBuffer(self, data):
        props = {}
        props["title"] = self._sanitize(data[0x20 : 0x20 + 20])
        props["code"] = self._sanitize(data[0x3c : 0x3c + 2])
        pub = data[0x38 : 0x38 + 4]
        props["publisher"] = n64_publishers.get(pub[3], "") # Low byte of int
        props["region"] = n64_regions.get(ord(data[0x3e]), "")
        if props["region"] or ord(data[0x3e]) in [0x00, 0x37]:
            props["region_code"] = "%02X" % ord(data[0x3e])
        else:
            props["region_code"] = ""
        return props

RomInfoParser.registerParser(Nintendo64Parser())


n64_regions = {
    0x00: None, # Demo games
    0x37: None, # Beta games
    0x41: "Japan/USA",
    0x44: "Germany",
    0x45: "USA",
    0x46: "France",
    0x49: "Italy",
    0x4A: "Japan",
    0x50: "Europe",
    0x53: "Spain",
    0x55: "Australia",
    0x59: "Australia",
    # Other PAL European codes
    0x58: "Europe",
    0x20: "Europe",
    0x21: "Europe",
    0x38: "Europe",
    0x70: "Europe",
}

n64_publishers = {
    "N": "Nintendo",
}
