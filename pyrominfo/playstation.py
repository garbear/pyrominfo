# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

from rominfo import RomInfoParser

class PlayStationParser(RomInfoParser):
    """
    Parse a Sony PlayStayion image. Valid extensions are iso, mdf, img, bin.
    PSX references and related source code:
    * mkpsxiso.c and lictool.c of the PSXSDK project:
    * https://code.google.com/p/psxsdk/source/browse/trunk/psxsdk/tools/mkpsxiso.c
    * https://code.google.com/p/psxsdk/source/browse/trunk/psxsdk/tools/lictool.c

    * mkpsxiso.java (Sorry for the zip link):
    * http://nic-nac-project.de/~sparrow/mkpsxiso-java-src-docs.zip

    * http://hitmen.c02.at/html/psx_sources.html
    * https://code.google.com/p/psxjin/

    * http://psxdev.net/forum/viewtopic.php?f=60&t=156
    """

    def getValidExtensions(self):
        return ["iso", "mdf", "img", "bin"]

    def parse(self, filename):
        props = {}
        with open(filename, "rb") as f:
            # 16 CD sectors of a RAW (bin, not iso) CD image
            data = bytearray(f.read(0x9300))
            if len(data) >= 0x9300:
                props = self.parseBuffer(data)
        return props

    def isValidData(self, data):
        """
        """
        return False

    def parseBuffer(self, data):
        props = {}

        if len(data) % 2352 == 0:
            data = self.toiso(data)

        # Psx BootEdit 2.0 Beta by loser 2000
        # Licensing region somehow affects data between 0024-24BE.
        #props["license_line1"] = self._sanitize(data[0x24d8 : 0x24d8 + 32]) # 0x2000 for iso
        #props["license_line2"] = self._sanitize(data[0x24f8 : 0x24f8 + 32]) # 0x2020 for iso
        props["license_line1"] = self._sanitize(data[0x2000 : 0x2000 + 32])
        props["license_line2"] = self._sanitize(data[0x2020 : 0x2020 + 32])

        return props

    def toiso(self, rawdata):
        """
        function name: http://baetzler.de/vidgames/psx_cd_faq.html
        """
        isodata = []
        for i in range(len(rawdata) // 2352):
            isodata.extend(rawdata[(i * 2352) + 24 : (i * 2352) + 24 + 2048])
        return isodata

RomInfoParser.registerParser(PlayStationParser())
