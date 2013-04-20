# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

from rominfo import RomInfoParser

class MasterSystemParser(RomInfoParser):
    """
    Parse a Sega Master System image. Valid extensions are sms, gg, sg (SG-1000 ROMs).
    TODO: Should we support SG-1000 ROMs?
    Sega Master System header references and related source code:
    * http://www.smspower.org/Development/ROMHeader
    * http://www.smspower.org/Development/SDSCHeader
    """

    def getValidExtensions(self):
        return ["sms", "gg", "sg"]

    def parse(self, filename):
        props = {}
        with open(filename, "rb") as f:
            data = bytearray(f.read())
            # First header check is at 0x1FF0, so we clearly need at least this much data
            if len(data) >= 0x2000:
                props = self.parseBuffer(data)
        return props

    def isValidData(self, data):
        """
        Sniff out Master System ROM header. Note that some ROMs may use
        custom text. Gensis Plus GX looks at addresses 0x1FF0, 0x3FF0, 0x7FF0.
        Quite a few ROMs, including "Strider (UE) [!].sms", use address 0x81F0.
        X-MAME 0.106 has code to check this address, but the code is commented out...
        https://code.oregonstate.edu/svn/dsp_bd/uclinux-dist/trunk/user/games/xmame/xmame-0.106/mess/machine/sms.c

        The SDSC tag was introduced in 2001 to provide a standard way to tag
        homebrew software. This tag is used as a fallback test if TMR SEGA isn't
        found.
        """
        if any(data[offset : offset + 8] == b"TMR SEGA" for offset in 0x1ff0, 0x3ff0, 0x7ff0, 0x81f0):
            return True
        if data[0x7fe0 : 0x7fe0 + 4] == b"SDSC":
            return True
        return False

    def parseBuffer(self, data):
        props = {}

        # Find Master System header offset (see isValidData(), default to 0x7FF0)
        offset = 0x7ff0
        for off in 0x1ff0, 0x3ff0, 0x81f0:
            if data[off : off + 8] == b"TMR SEGA":
                offset = off
                break
        header = data[offset : offset + 0x10] # Only need 0x10 (16) bytes
        if not header:
            return props

        # 7FF0-7FF7 - Magic word "TMR SEGA". Sometimes, this is customized as a "signature"
        #             along with the reserved space and checksum (thus invalidating the
        #             checksum). No names-in-headers lookup tables are maintained here,
        #             but the information from the header_id, reserved_word and
        #             checksum_ascii fields can be referenced against data gathered at:
        #             * http://www.smspower.org/Development/NamesInHeaders
        #             * http://www.smspower.org/forums/viewtopic.php?t=2407
        props["header_id"] = self._sanitize(header[ : 8])

        # 7FF8-7FF9 - Reserved space, usually 0x0000, 0xFFFF or 0x2020
        props["reserved_word"] = self._sanitize(header[0x08 : 0x08 + 2])

        # 7FFA-7FFB - Checksum, little endian
        props["checksum"] = "%04X" % (header[0x0a] << 8 | header[0x0b])

        # Also include checksum in ASCII. Some programmers, like Yuji Naka, use the
        # reserved space and checksum as a signature (NAKA), so in this case KA is
        # more convenient than 0x4B41. According to www.smspower.org, these signatures
        # only seem to feature A-Z, 0-9 and /.
        word = self._sanitize(header[0x0a : 0x0a + 2])
        props["checksum_ascii"] = [c for c in word if 'A' <= c and c <= 'Z' or '0' <= c and c <= '9' or c == '/']

        # 7FFC-7FFE.8 - Product code. The first 2 bytes are a Binary Coded Decimal
        #               representation of the last four digits of the product code.
        #               The high 4 bits of the next byte are a hexadecimal representation
        #               of any remaining digits of the product code.
        props["code"] = "%02d%02X%02X" % (header[0x0e] >> 4, header[0x0d], header[0x0c])

        # 7FFE.8 - Version. The low 4 bits give a version number
        props["version"] = "%02X" % (header[0x0e] & 0x0f)

        # 7FFF.8 - Region and system for which the cartridge is intended
        r = (header[0x0f] >> 4)
        props["console"] = "Sega Master System" if r in [3, 4] else "Game Gear" if r in [5, 6, 7] else ""
        props["region"] = "Japan" if r in [3, 5] else "Export" if r in [4, 6] else "International" if r == 7 else ""

        # 7FFF.8 - ROM size. Final 4 bits give the ROM size, some values are buggy.
        #          It is common for this value to be present even when the checksum is not.
        #          It is also common for it to indicate a ROM size smaller than the actual ROM
        #          size, perhaps to speed up the boot process by speeding up the checksum validation.
        props["rom_size"] = mastersystem_romsize.get(header[0x0f] & 0x0f, "")

        # SDSC (homebrew) header. See isValidData()
        if data[0x7fe0 : 0x7fe0 + 4] == b"SDSC" and len(data) > 0x7fe0 + 0x10:
            sdsc = data[0x7fe0 : 0x7fe0 + 0x10]
            # 7FE0-7FE3 - Magic word "SDSC", this is used to show that the header is present
            # 7FE4-7FE5 - Version, major-dot-minor in BCD. Thus, 0x1046 is 10.46. Note,
            #             this version tag will override the SMS header tag (probably
            #             as the author intended).
            props["version"] = "%X.%02X" % (sdsc[0x04], sdsc[0x05])

            # 7FE6-7FE9 - Release/compilation date, in day, month, year (little endian, all BCD)
            props["date"] = "%02X%02X-%02X-%02X" % (sdsc[0x09], sdsc[0x08], sdsc[0x07], sdsc[0x06])

            # 7FEA-7FEB - Author pointer, the ROM address of a zero-terminated
            #             author name. 0xFFFF and 0x0000 indicate no author name.
            props["author"] = self.get_cstr(sdsc[0x0a] << 8 | sdsc[0x0b], data)

            # 7FEC-7FED - Name pointer, the ROM address of a zero-terminated program
            #             name. 0xFFFF indicates no program name (but I ignore 0 also).
            props["title"] = self.get_cstr(sdsc[0x0c] << 8 | sdsc[0x0d], data)

            # 7FEE-7FEF - Description pointer, the ROM address of a zero-terminated
            #             description. 0xFFFF indicates no program name (but I ignore
            #             0x0000 also). Can include CR, CRLF and LF line breaks.
            props["description"] = self.get_cstr(sdsc[0x0e] << 8 | sdsc[0x0f], data)
        else:
            # No update to version property
            props["date"] = ""
            props["author"] = ""
            props["title"] = ""
            props["description"] = ""

        return props

    def get_cstr(self, ptr, data):
        """
        Parse a zero-terminated (c-style) string from a bytearray. 0xFFFF and
        0x0000 are invalid ptr values and will return "".
        """
        if ptr != 0xffff and ptr != 0 and ptr < len(data):
            term = ptr
            while term < len(data) and data[term]:
                term += 1
            return self._sanitize(data[ptr : term])
        return ""
        

RomInfoParser.registerParser(MasterSystemParser())


mastersystem_romsize = {
    0xa: "8 KB",
    0xb: "16 KB",
    0xc: "32 KB",
    0xd: "48 KB",
    0xe: "64 KB",
    0xf: "128 KB",
    0x0: "256 KB",
    0x1: "512 KB",
    0x2: "1024 KB",
}
