# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

from rominfo import RomInfoParser

from hachoir_core.field.field import MissingField

from hachoir_parser import createParser#, HachoirParserList, ValidateError
from hachoir_metadata import metadata, metadata_item

class PlayStationParser(RomInfoParser):
    """
    Parse a Sony PlayStayion image. Valid extensions are iso, mdf, img, bin.
    PSX references and related source code:
    * mkpsxiso.c and lictool.c of the PSXSDK project:
    * https://code.google.com/p/psxsdk/source/browse/trunk/psxsdk/tools/mkpsxiso.c
    * https://code.google.com/p/psxsdk/source/browse/trunk/psxsdk/tools/lictool.c

    * http://hitmen.c02.at/html/psx_sources.html
    * https://code.google.com/p/psxjin/

    * http://psxdev.net/forum/viewtopic.php?f=60&t=156
    """

    def getValidExtensions(self):
        return ["iso", "mdf", "img", "bin"]

    def parse(self, filename):
        props = {}
        with open(filename, "rb") as f:
            ext = self._getExtension(filename)
            sectorsize = 2352 if ext == "bin" else 2048 if ext == "iso" else 0 # 0 reads entire CD image
            # The first 16 sectors of a PSX disc are the "boot" blocks
            data = bytearray(f.read(16 * sectorsize))
            if len(data):
                props = self.parseBuffer(data)

                parser = createParser(unicode(filename), real_filename=filename)
                parser.createFields()
                print "path_table_size_l: %s" % parser["/volume[0]/content/path_table_size_l"].value
                print "path_table_size_m: %s" % parser["/volume[0]/content/path_table_size_m"].value
                lba = parser["/volume[0]/content/occu_lpath"].value
                print "occu_lpath: %d (%d)" % (lba, lba * 2048)
                lba_m = parser["/volume[0]/content/occu_mpath"].value
                print "occu_mpath: %d (%d)" % (lba_m, lba_m * 2048)

                i = 0
                while True:
                    path = "path[%d]/" % i
                    try:
                        print path + "length: %s" % parser[path + "length"].value
                        print path + "name: %s" % parser[path + "name"].value
                        print path + "location: %s" % parser[path + "location"].value
                        print path + "parent_dir: %s" % parser[path + "parent_dir"].value
                    except MissingField:
                        break
                    i += 1

                # Get SYSTEM.CNF
                # find line BOOT=cdrom:\psx.exe;1
                # default is \PSX.EXE
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
        #for i in range(len(data) // 2352):
        #    data[i * 2352 : i * 2352 + 2352] = data[i * 2352 + 24 : i * 2352 + 24 + 2048]

        isodata = []
        for i in range(len(rawdata) // 2352):
            isodata.extend(rawdata[(i * 2352) + 24 : (i * 2352) + 24 + 2048])
        return isodata



RomInfoParser.registerParser(PlayStationParser())
