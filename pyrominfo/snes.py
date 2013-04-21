# Copyright (C) 1997-2007 ZSNES Team (zsKnight, _Demo_, pagefault, Nach)
# Copyright (C) 2013      Garrett Brown
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from rominfo import RomInfoParser

class SNESParser(RomInfoParser):
    """
    Parse a SNES image. Valid extensions are smc, swc, fig.
    SNES header references and related source code:
    * http://romhack.wikia.com/wiki/SNES_header
    * http://softpixel.com/~cwright/sianse/docs/Snesrom.txt
    * initc.c of the ZSNES project:
    * http://zsnes.cvs.sourceforge.net/viewvc/zsnes/zsnes/src/initc.c?view=markup
    * memmap.cpp of the Snes9x project:
    * https://github.com/snes9xgit/snes9x/blob/master/memmap.cpp
    * snescart.c of the MAME project:
    * http://mamedev.org/source/src/mess/machine/snescart.c.html
    """

    # Enum values
    FORMAT_LoROM = 0
    FORMAT_HiROM = 1

    FORMAT_SMALLFIRST = 0
    FORMAT_BIGFIRST = 1

    def getValidExtensions(self):
        return ["smc", "swc", "fig"]

    def parse(self, filename):
        props = {}
        with open(filename, "rb") as f:
            data = bytearray(f.read())
            if len(data):
                props = self.parseBuffer(data)
        return props

    def isValidData(self, data):
        if len(data):
            if self.hasSMCHeader(data):
                return True
            # TODO: Need more conclusive tests
            return False
        return False

    def parseBuffer(self, romdata):
        props = {}
        forceInterleavedOff = False

        while True:
            # Check for a header (512 bytes), and skip it if found
            data = romdata[512:] if self.hasSMCHeader(romdata) else romdata[:]

            (hiScore, loScore, extendedFormat, headerOffsetRef) = self.findHiLoMode(data, forceInterleavedOff)

            # These two games fail to be detected (Source: Snes9x)
            if data[0x7fc0 : 0x7fc0 + 22] == b"YUYU NO QUIZ DE GO!GO!" or \
               data[0xffc0 : 0xffc0 + 21] == b"BATMAN--REVENGE JOKER":
                (mapType, interleaved, tales) = (SNESParser.FORMAT_LoROM, False, False)
            else:
                (mapType, interleaved, tales) = self.findMemoryModel(data[headerOffsetRef : ], hiScore, loScore)

            if not forceInterleavedOff and interleaved:
                mapType = self.convertInterleaved(data, extendedFormat, mapType, tales)

                # Modifying ROM, so we need to re-score
                hiScore = self.scoreHiRom(data)
                loScore = self.scoreLoRom(data)

                if (mapType == SNESParser.FORMAT_HiROM and (loScore >= hiScore or hiScore < 0)) or \
                   (mapType == SNESParser.FORMAT_LoROM and (hiScore >  loScore or loScore < 0)):
                    # Game image lied about its type! Trying again...
                    forceInterleavedOff = True
                    continue

            if tales or extendedFormat == SNESParser.FORMAT_SMALLFIRST:
                # Fix swapped ExHiROM
                tmp = data[ : -0x400000]
                tmp2 = data[-0x400000 : ]
                data[ : 0x400000] = tmp2
                data[0x400000 : ] = tmp

            if data[0x7fc0 : 0x7fc0 + 21] == b"Satellaview BS-X     ":
                bs = True
                bsHeader = False
                mapType = SNESParser.FORMAT_LoROM
            else:
                bLo = (self.isBSX(data[0x7fc0 : 0x7fc0 + 0x1b]) == 1)
                bHi = (self.isBSX(data[0xffc0 : 0xffc0 + 0x1b]) == 1)
                bs = bLo or bHi
                bsHeader = bs
                if bs:
                    mapType = SNESParser.FORMAT_LoROM if bLo else SNESParser.FORMAT_HiROM

            # Re-calculate the header offset (include extended header, 0x10
            # bytes before the actual 64-byte SNES header starts)
            # See http://romhack.wikia.com/wiki/SNES_header#Extended_header_.28bytes_.24ffb2...24ffb5.29
            headerOffset = 0x7fb0
            if extendedFormat == SNESParser.FORMAT_BIGFIRST:
                headerOffset += 0x400000
            if mapType == SNESParser.FORMAT_HiROM:
                headerOffset += 0x8000
            header = data[headerOffset : ]

            # Instead of branching on bsHeader, simply apply the different
            # values to the ROM data and use the same code below to set props
            if bsHeader: # The BS game's SRAM was not found
                # Only use the first 16 of 21 title characters
                header[0x010 + 16, 0x010 + 21] = b"     "
                # Rom speed flag uses 0x28 (RAM size?) instead of 0x25
                header[0x25] = header[0x28]
                # Cartridge type is specific to Satellaview BS-X
                header[0x26] = 0xE5
                # Rom size (Is this correct?)
                p = 0
                while (1 << p) < len(data):
                    p += 1
                header[0x27] = max(p - 10, 8) # 0x08 is the min according to romhack.wikia.com
                # Ram size is 256 Kbit (standard for most copiers according to Snesrom.txt)
                header[0x28] = 0x05
                # Region is hard-coded to Japan apparently
                header[0x29] = 0

            # Remember, addresses start at 000, but extended headers are padded by 0x10 bytes
            # See http://romhack.wikia.com/wiki/SNES_header

            # 000-014 - Title, UPPER CASE ASCII
            props["title"] = self._sanitize(header[0x10 : 0x10 + 21])

            # Game code - part of the extended header, not always present
            props["code"] = self._sanitize(header[0x02 : 0x02 + 4])

            # 015 - ROM layout and ROM speed, a bitwise-or of these flags:
            #       0x20 is always set
            #       0x10 is set when using FastROM
            #       0x01 is set for HiROM or cleared for LoROM
            HiROM = "ExHiROM" if extendedFormat else "HiROM"
            props["memory_layout"] = HiROM if mapType == SNESParser.FORMAT_HiROM else "LoROM"
            props["rom_speed"] = "FastROM" if (header[0x25] & 0x10) else "SlowROM"

            # 016 - Cartridge type, values greater than 0x02 indicate special add-on hardware in the cartridge
            props["cartridge_type"] = self.getCartridgeType(header, bs)

            # 017 - ROM size: 1 << (ROM_SIZE - 7) Mbits, range is 8..12 (256KB..4MB, 2Mb..32Mb)
            b = header[0x27]
            props["rom_size"] = "%d Mbit" % (1 << (b - 7)) if (8 <= b and b <= 12) else ""

            # 018 - RAM size: 1 << (3 + SRAM_BYTE) Kbits, range is 0..5 (0..32 kilobytes, 0..256 kbit)
            props["ram_size"] = "%d Kbit" % (1 << (3 + header[0x28])) if header[0x28] <= 5 else ""

            # 019 - Country code, video region
            props["region"] = snes_regions.get(header[0x29], "")
            props["video_output"] = "NTSC" if header[0x29] in [0, 1, 13] else "PAL" if header[0x29] < 13 else ""

            # 01A - Licensee code 0x33 implies an extended header at bytes ffb0..ffbf
            company = self.getCompanyCode(header)
            props["publisher"] = snes_publishers.get(company, "")
            props["publisher_code"] = ("%04X" % company) if company != -1 else ""

            # 01B - Version, typically contains 0x00. Most ROM hackers never touch this
            #       byte, so multiple versions of a ROM hack may share the same value
            props["version"] = "%02X" % header[0x2b]

            # 01C-01F - Checksum complement and checksum, respectively. The checksum is
            #           the unsigned little-endian 16-bit sum of the values of the bytes
            #           in the ROM. If the size of the ROM is not a power of 2, then some
            #           bytes may enter the sum multiple times through mirroring. The
            #           checksum complement is the bitwise-xor of the checksum with 0xFFFF.
            props["checksum"] = "%04X" % (header[0x2e] + (header[0x2f] << 8))
            props["checksum_complement"] = "%04X" % (header[0x2c] + (header[0x2d] << 8))

            return props

    def hasSMCHeader(self, data):
        """
        Check for a 512-byte SMC, SWC or FIG header prepended to the beginning
        of the file.
        """
        if 512 <= len(data):
            if data[8] == 0xaa and data[9] == 0xbb and data[10] == 0x04:
                # Found an SMC/SWC identifier (Source: MAME and ZSNES)
                return True
            if (data[4], data[5]) in [(0x00, 0x80), (0x11, 0x02), (0x47, 0x83), (0x77, 0x83), \
                                      (0xDD, 0x02), (0xDD, 0x82), (0xF7, 0x83), (0xFD, 0x82)]:
                # Found a FIG header (Source: ZSNES)
                return True
            if data[1] << 8 | data[0] == (len(data) - 512) >> 13:
                # Some headers have the rom size at the start, if this matches with
                # the actual rom size, we probably have a header (Source: MAME)
                return True
            if len(data) % 0x8000 == 512:
                # As a last check we'll see if there's exactly 512 bytes extra
                # to this image. MAME takes len modulus 0x8000 (32kb), Snes9x
                # uses len / 0x2000 (8kb) * 0x2000.
                return True
        return False

    def deinterleaveType1(self, data, size):
        """
        Swap blocks in a range of ROM memory.
        """
        nbanks = size >> 15
        nblocks = nbanks >> 2
        blocks = [(i >> 1) + nblocks if i % 2 == 0 else i >> 1 for i in range(nblocks * 2)]
        for i in range(nblocks * 2):
            for j in range(nblocks * 2):
                if blocks[j] == i:
                    tmp = data[blocks[j] * 0x8000 : blocks[j] * 0x8000 + 0x8000]
                    data[blocks[j] * 0x8000 : blocks[j] * 0x8000 + 0x8000] = \
                        data[blocks[i] * 0x8000 : blocks[i] * 0x8000 + 0x8000]
                    data[blocks[i] * 0x8000 : blocks[i] * 0x8000 + 0x8000] = tmp
                    b = blocks[j]
                    blocks[j] = blocks[i]
                    blocks[i] = b
                    break

    def findHiLoMode(self, data, forceInterleavedOff):
        hiScore = self.scoreHiRom(data)
        loScore = self.scoreLoRom(data)
        extendedFormat = False
        headerOffsetRef = 0

        if len(data) > 0x400000 and \
                data[0x7fd5] + (data[0x7fd6] << 8) not in [0x3423, 0x3523, 0x4332, 0x4532] and \
                data[0xffd5] + (data[0xffd6] << 8) not in [0xf93a, 0xf53a]:
            swappedHiRom = self.scoreHiROM(data, 0x400000)
            swappedLoRom = self.scoreLoROM(data, 0x400000)
            if max(swappedLoRom, swappedHiRom) >= max(loScore, hiScore):
                extendedFormat = SNESParser.FORMAT_BIGFIRST
                hiScore = swappedHiRom
                loScore = swappedLoRom
                headerOffsetRef = 0x400000
            else:
                extendedFormat = SNESParser.FORMAT_SMALLFIRST

        elif data[0x7ffc] + (data[0x7ffd] << 8) < 0x8000 and \
             data[0xfffc] + (data[0xfffd] << 8) < 0x8000 and not forceInterleavedOff:
            # If both vectors are invalid, it's type 1 interleaved LoROM
            self.deinterleaveType1(data, len(data));
            # Modifying ROM, so we need to re-score
            hiScore = self.scoreHiRom(data)
            loScore = self.scoreLoRom(data)

        return (hiScore, loScore, extendedFormat, headerOffsetRef,)

    def findMemoryModel(self, data, hiScore, loScore):
        """
        Determine if the ROM is a LoROM Memory Model (32k Banks) or HiROM
        Memory Model (64k Banks).
        """
        mapType = None # SNESParser.FORMAT_LoROM or SNESParser.FORMAT_HiROM
        interleaved = False
        tales = False

        if loScore >= hiScore:
            mapType = SNESParser.FORMAT_LoROM
            # Ignore map type byte if not 0x2x or 0x3x
            if data[0x7fd5] & 0xf0 in [0x20, 0x30]:
                if data[0x7fd5] & 0x0f == 1:
                    interleaved = True
                elif data[0x7fd5] & 0x0f == 5:
                    interleaved = True
                    tales = True
        else:
            mapType = SNESParser.FORMAT_HiROM
            if data[0xffd5] & 0xf0 in [0x20, 0x30]:
                if data[0xffd5] & 0x0f in [0, 3]:
                    interleaved = True

        return (mapType, interleaved, tales,)

    def convertInterleaved(self, data, extendedFormat, oldMapType, tales):
        # ROM image is in interleaved format, converting...
        if tales:
            if extendedFormat == SNESParser.FORMAT_BIGFIRST:
                self.deinterleaveType1(data, 0x400000)
                tmpdata = data[0x400000 : ]
                self.deinterleaveType1(tmpdata, len(data))
                data[0x400000 : ] = tmpdata
            else:
                self.deinterleaveType1(data, len(data) - 0x400000)
                tmpdata = data[len(data) - 0x400000 : ]
                self.deinterleaveType1(tmpdata, 0x400000)
                data[len(data) - 0x400000 : ] = tmpdata
            return SNESParser.FORMAT_HiROM
        else:
            # Swap memory models
            self.deinterleaveType1(data, len(data));
            return SNESParser.FORMAT_LoROM if oldMapType == SNESParser.FORMAT_HiROM else SNESParser.FORMAT_HiROM

    def scoreHiRom(self, data, offset=0):
        size = len(data)
        data = data[0xff00 + offset : ]
        score = 0

        if data[0xd4] == 0x20:
            score += 2
        if data[0xd5] & 0x1:
            score += 2
        # Mode23 is SA-1
        if data[0xd5] == 0x23:
            score -= 2
        if data[0xd5] & 0xf < 4:
            score += 2
        if 1 << max(data[0xd7] - 7, 0) > 48:
            score -= 1
        if data[0xda] == 0x33:
            score += 2
        if data[0xdc] + (data[0xdd] << 8) + data[0xde] + (data[0xdf] << 8) == 0xffff:
            score += 2
            if data[0xde] + (data[0xdf] << 8) != 0:
                score += 1
        if data[0xfc] + (data[0xfd] << 8) > 0xffb0: 
            score -= 2
        if not (data[0xfd] & 0x80):
            score -= 6
        if not self._allASCII(data[0xb0 : 0xb0 + 6]):
            score -= 1
        if not self._allASCII(data[0xc0 : 0xc0 + 22]):
            score -= 1
        if size > 1024 * 1024 * 3:
            score += 4
        return score

    def scoreLoRom(self, data, offset=0):
        size = len(data)
        data = data[0x7f00 + offset : ]
        score = 0

        if not (data[0xd5] & 0x1):
            score += 3
        # Mode23 is SA-1
        if data[0xd5] == 0x23:
            score += 2
        if data[0xd5] & 0xf < 4:
            score += 2
        if 1 << max(data[0xd7] - 7, 0) > 48:
            score -= 1
        if data[0xda] == 0x33:
            score += 2
        if data[0xdc] + (data[0xdd] << 8) + data[0xde] + (data[0xdf] << 8) == 0xffff:
            score += 2
            if data[0xde] + (data[0xdf] << 8) != 0:
                score += 1
        if data[0xfc] + (data[0xfd] << 8) > 0xffb0: 
            score -= 2
        if not (data[0xfd] & 0x80):
            score -= 6
        if not self._allASCII(data[0xb0 : 0xb0 + 6]):
            score -= 1
        if not self._allASCII(data[0xc0 : 0xc0 + 22]):
            score -= 1
        if size <= 1024 * 1024 * 16:
            score += 2
        return score

    def isBSX(self, data):
        """"
        Only need the first 0x1B (27) bytes of data to test for BS-X BIOSes.
        """
        if (data[0x15] == 0 or data[0x15] & 0x83 == 80) and data[0x18] in [0x20, 0x21, 0x30, 0x31] and \
                data[0x1a] in [0x33, 0xff]:
            if data[0x16] == 0 and data[0x17] == 0:
                return 2
            if (data[0x16] == 0xff and data[0x17] == 0xff) or (data[0x16] & 0x0f == 0 and data[0x16] >> 4 < 13):
                return 1
        return 0

    def getCartridgeType(self, header, bs):
        romSpeed = header[0x25]
        romType = header[0x26]

        if romType == 0 and not bs:
            kart = "ROM"
        else:
            identifier = ((romType & 0xff) << 8) + (romSpeed & 0xff)
            contents = ["ROM", "ROM+RAM", "ROM+RAM+BATT"]
            chip = ""

            if bs:
                chip = "BS"
            elif identifier in [0x1320, 0x1420, 0x1520, 0x1A20]:
                chip = "SuperFX"
                # Set the SRAM size
                if header[0x2a] == 0x33:
                    header[0x28] = header[0x2b] # version
                else:
                    header[0x28] = 0x05 # 256 Kbit
                header[0x28] = 2
            elif identifier in [0x4332, 0x4532]:
                chip = "SDD1"
            elif identifier == 0x2530:
                chip = "OBC1"
            elif identifier in [0x3423, 0x3523]:
                chip = "SA1"
            elif identifier == 0xF93A:
                chip = "SPC7110+RTC"
            elif identifier == 0xF53A:
                chip = "SPC7110"
            elif identifier == 0x5535:
                chip = "SRTC"
            elif identifier == 0xF320:
                chip = "C4"
            elif identifier == 0xF630:
                # header[0x27] == 0x09 is ROM Size of 4 Mbit
                chip = "ST-011" if header[0x27] == 0x09 else "ST-010"
            elif identifier == 0xF530:
                chip = "ST-018"
                # Set the SRAM  size to 32 Kbit
                header[0x28] = 0x02
            elif romType == 0x03:
                if romSpeed == 0x30:
                    chip = "DSP-4"
                else:
                    chip = "DSP-1"
            elif romType == 0x05:
                if romSpeed == 0x20:
                    chip = "DSP-2"
                elif romSpeed == 0x30 and header[0x2a] == 0xb2:
                    chip = "DSP-3"
                else:
                    chip = "DSP-1"
            if chip:
                kart = "%s+%s" % (contents[(romType & 0xf) % 3], chip)
            else:
                kart = contents[(romType & 0xf) % 3]
        return kart

    def getCompanyCode(self, header):
        companyCode = -1
        if header[0x2a] != 0x33:
            companyCode = ((header[0x2a] >> 4) & 0x0F) * 36 + (header[0x2a] & 0x0F)
        else:
            l = chr(header[0x00]).upper()
            r = chr(header[0x01]).upper()
            l2 = ord(l) - ord('7') if l > '9' else ord(l) - ord('0')
            r2 = ord(r) - ord('7') if r > '9' else ord(r) - ord('0')
            companyCode = l2 * 36 + r2 if l2 >= 0 and r2 >= 0 else -1
        return companyCode

RomInfoParser.registerParser(SNESParser())


# Souce: http://softpixel.com/~cwright/sianse/docs/Snesrom.txt
# Snesrom.txt correction: South Korea should be NTSC
snes_regions = {
    0: "Japan",                       # NTSC
    1: "USA/Canada",                  # NTSC
    2: "Europe/Asia/Oceania",         # PAL
    3: "Sweden",                      # PAL
    4: "Finland",                     # PAL
    5: "Denmark",                     # PAL
    6: "France",                      # PAL
    7: "Holland",                     # PAL
    8: "Spain",                       # PAL
    9: "Germany/Austria/Switzerland", # PAL
    10: "Italy",                      # PAL
    11: "Hong Kong/China",            # PAL
    12: "Indonesia",                  # PAL
    13: "South Korea",                # NTSC
}

# Source: Snes9x
snes_publishers = {
    # ID 0x0000 is for Unlicensed ROMs
    0x0001: "Nintendo",
    0x0002: "Rocket Games/Ajinomoto",
    0x0003: "Imagineer-Zoom",
    0x0004: "Gray Matter",
    0x0005: "Zamuse",
    0x0006: "Falcom",
    0x0008: "Capcom",
    0x0009: "Hot B Co.",
    0x000a: "Jaleco",
    0x000b: "Coconuts Japan",
    0x000c: "Coconuts Japan/G.X.Media",
    0x000d: "Micronet",
    0x000e: "Technos",
    0x000f: "Mebio Software",
    0x0010: "Shouei System",
    0x0011: "Starfish",
    0x0013: "Mitsui Fudosan/Dentsu",
    0x0015: "Warashi Inc.",
    0x0017: "Nowpro",
    0x0019: "Game Village",
    0x001a: "IE Institute",
    0x0024: "Banarex",
    0x0025: "Starfish",
    0x0026: "Infocom",
    0x0027: "Electronic Arts Japan",
    0x0029: "Cobra Team",
    0x002a: "Human/Field",
    0x002b: "KOEI",
    0x002c: "Hudson Soft",
    0x002d: "S.C.P./Game Village",
    0x002e: "Yanoman",
    0x0030: "Tecmo Products",
    0x0031: "Japan Glary Business",
    0x0032: "Forum/OpenSystem",
    0x0033: "Virgin Games (Japan)",
    0x0034: "SMDE",
    0x0035: "Yojigen",
    0x0037: "Daikokudenki",
    0x003d: "Creatures Inc.",
    0x003e: "TDK Deep Impresion",
    0x0048: "Destination Software/KSS",
    0x0049: "Sunsoft/Tokai Engineering",
    0x004a: "POW (Planning Office Wada)/VR 1 Japan",
    0x004b: "Micro World",
    0x004d: "San-X",
    0x004e: "Enix",
    0x004f: "Loriciel/Electro Brain",
    0x0050: "Kemco Japan",
    0x0051: "Seta Co.,Ltd.",
    0x0052: "Culture Brain",
    0x0053: "Irem Corp.",
    0x0054: "Palsoft",
    0x0055: "Visit Co., Ltd.",
    0x0056: "Intec",
    0x0057: "System Sacom",
    0x0058: "Poppo",
    0x0059: "Ubisoft Japan",
    0x005b: "Media Works",
    0x005c: "NEC InterChannel",
    0x005d: "Tam",
    0x005e: "Gajin/Jordan",
    0x005f: "Smilesoft",
    0x0062: "Mediakite",
    0x006c: "Viacom",
    0x006d: "Carrozzeria",
    0x006e: "Dynamic",
    0x0070: "Magifact",
    0x0071: "Hect",
    0x0072: "Codemasters",
    0x0073: "Taito/GAGA Communications",
    0x0074: "Laguna",
    0x0075: "Telstar Fun & Games/Event/Taito",
    0x0077: "Arcade Zone Ltd.",
    0x0078: "Entertainment International/Empire Software",
    0x0079: "Loriciel",
    0x007a: "Gremlin Graphics",
    0x0090: "Seika Corp.",
    0x0091: "UBI SOFT Entertainment Software",
    0x0092: "Sunsoft US",
    0x0094: "Life Fitness",
    0x0096: "System 3",
    0x0097: "Spectrum Holobyte",
    0x0099: "Irem",
    0x009b: "Raya Systems",
    0x009c: "Renovation Products",
    0x009d: "Malibu Games",
    0x009f: "Eidos/U.S. Gold",
    0x00a0: "Playmates Interactive",
    0x00a3: "Fox Interactive",
    0x00a4: "Time Warner Interactive",
    0x00aa: "Disney Interactive",
    0x00ac: "Black Pearl",
    0x00ae: "Advanced Productions",
    0x00b1: "GT Interactive",
    0x00b2: "RARE",
    0x00b3: "Crave Entertainment",
    0x00b4: "Absolute Entertainment",
    0x00b5: "Acclaim",
    0x00b6: "Activision",
    0x00b7: "American Sammy",
    0x00b8: "Take 2/GameTek",
    0x00b9: "Hi Tech",
    0x00ba: "LJN Ltd.",
    0x00bc: "Mattel",
    0x00be: "Mindscape/Red Orb Entertainment",
    0x00bf: "Romstar",
    0x00c0: "Taxan",
    0x00c1: "Midway/Tradewest",
    0x00c3: "American Softworks Corp.",
    0x00c4: "Majesco Sales Inc.",
    0x00c5: "3DO",
    0x00c8: "Hasbro",
    0x00c9: "NewKidCo",
    0x00ca: "Telegames",
    0x00cb: "Metro3D",
    0x00cd: "Vatical Entertainment",
    0x00ce: "LEGO Media",
    0x00d0: "Xicat Interactive",
    0x00d1: "Cryo Interactive",
    0x00d4: "Red Storm Entertainment",
    0x00d5: "Microids",
    0x00d7: "Conspiracy/Swing",
    0x00d8: "Titus",
    0x00d9: "Virgin Interactive",
    0x00da: "Maxis",
    0x00dc: "LucasArts Entertainment",
    0x00df: "Ocean",
    0x00e1: "Electronic Arts",
    0x00e3: "Laser Beam",
    0x00e6: "Elite Systems",
    0x00e7: "Electro Brain",
    0x00e8: "The Learning Company",
    0x00e9: "BBC",
    0x00eb: "Software 2000",
    0x00ed: "BAM! Entertainment",
    0x00ee: "Studio 3",
    0x00f2: "Classified Games",
    0x00f4: "TDK Mediactive",
    0x00f6: "DreamCatcher",
    0x00f7: "JoWood Produtions",
    0x00f8: "SEGA",
    0x00f9: "Wannado Edition",
    0x00fa: "LSP (Light & Shadow Prod.)",
    0x00fb: "ITE Media",
    0x00fc: "Infogrames",
    0x00fd: "Interplay",
    0x00fe: "JVC (US)",
    0x00ff: "Parker Brothers",
    0x0101: "SCI (Sales Curve Interactive)/Storm",
    0x0104: "THQ Software",
    0x0105: "Accolade Inc.",
    0x0106: "Triffix Entertainment",
    0x0108: "Microprose Software",
    0x0109: "Universal Interactive/Sierra/Simon & Schuster",
    0x010b: "Kemco",
    0x010c: "Rage Software",
    0x010d: "Encore",
    0x010f: "Zoo",
    0x0110: "Kiddinx",
    0x0111: "Simon & Schuster Interactive",
    0x0112: "Asmik Ace Entertainment Inc./AIA",
    0x0113: "Empire Interactive",
    0x0116: "Jester Interactive",
    0x0118: "Rockstar Games",
    0x0119: "Scholastic",
    0x011a: "Ignition Entertainment",
    0x011b: "Summitsoft",
    0x011c: "Stadlbauer",
    0x0120: "Misawa",
    0x0121: "Teichiku",
    0x0122: "Namco Ltd.",
    0x0123: "LOZC",
    0x0124: "KOEI",
    0x0126: "Tokuma Shoten Intermedia",
    0x0127: "Tsukuda Original",
    0x0128: "DATAM-Polystar",
    0x012b: "Bullet-Proof Software",
    0x012c: "Vic Tokai Inc.",
    0x012e: "Character Soft",
    0x012f: "I'Max",
    0x0130: "Saurus",
    0x0133: "General Entertainment",
    0x0136: "I'Max",
    0x0137: "Success",
    0x0139: "SEGA Japan",
    0x0144: "Takara",
    0x0145: "Chun Soft",
    0x0146: "Video System Co., Ltd./McO'River",
    0x0147: "BEC",
    0x0149: "Varie",
    0x014a: "Yonezawa/S'pal",
    0x014b: "Kaneko",
    0x014d: "Victor Interactive Software/Pack-in-Video",
    0x014e: "Nichibutsu/Nihon Bussan",
    0x014f: "Tecmo",
    0x0150: "Imagineer",
    0x0153: "Nova",
    0x0154: "Den'Z",
    0x0155: "Bottom Up",
    0x0157: "TGL (Technical Group Laboratory)",
    0x0159: "Hasbro Japan",
    0x015b: "Marvelous Entertainment",
    0x015d: "Keynet Inc.",
    0x015e: "Hands-On Entertainment",
    0x0168: "Telenet",
    0x0169: "Hori",
    0x016c: "Konami",
    0x016d: "K.Amusement Leasing Co.",
    0x016e: "Kawada",
    0x016f: "Takara",
    0x0171: "Technos Japan Corp.",
    0x0172: "JVC (Europe/Japan)/Victor Musical Industries",
    0x0174: "Toei Animation",
    0x0175: "Toho",
    0x0177: "Namco",
    0x0178: "Media Rings Corp.",
    0x0179: "J-Wing",
    0x017b: "Pioneer LDC",
    0x017c: "KID",
    0x017d: "Mediafactory",
    0x0181: "Infogrames Hudson",
    0x018c: "Acclaim Japan",
    0x018d: "ASCII Co./Nexoft",
    0x018e: "Bandai",
    0x0190: "Enix",
    0x0192: "HAL Laboratory/Halken",
    0x0193: "SNK",
    0x0195: "Pony Canyon Hanbai",
    0x0196: "Culture Brain",
    0x0197: "Sunsoft",
    0x0198: "Toshiba EMI",
    0x0199: "Sony Imagesoft",
    0x019b: "Sammy",
    0x019c: "Magical",
    0x019d: "Visco",
    0x019f: "Compile",
    0x01a1: "MTO Inc.",
    0x01a3: "Sunrise Interactive",
    0x01a5: "Global A Entertainment",
    0x01a6: "Fuuki",
    0x01b0: "Taito",
    0x01b2: "Kemco",
    0x01b3: "Square",
    0x01b4: "Tokuma Shoten",
    0x01b5: "Data East",
    0x01b6: "Tonkin House",
    0x01b8: "KOEI",
    0x01ba: "Konami/Ultra/Palcom",
    0x01bb: "NTVIC/VAP",
    0x01bc: "Use Co., Ltd.",
    0x01bd: "Meldac",
    0x01be: "Pony Canyon (Japan)/FCI (US)",
    0x01bf: "Angel/Sotsu Agency/Sunrise",
    0x01c0: "Yumedia/Aroma Co., Ltd.",
    0x01c3: "Boss",
    0x01c4: "Axela/Crea-Tech",
    0x01c5: "Sekaibunka-Sha/Sumire kobo/Marigul Management Inc.",
    0x01c6: "Konami Computer Entertainment Osaka",
    0x01c9: "Enterbrain",
    0x01d4: "Taito/Disco",
    0x01d5: "Sofel",
    0x01d6: "Quest Corp.",
    0x01d7: "Sigma",
    0x01d8: "Ask Kodansha",
    0x01da: "Naxat",
    0x01db: "Copya System",
    0x01dc: "Capcom Co., Ltd.",
    0x01dd: "Banpresto",
    0x01de: "TOMY",
    0x01df: "Acclaim/LJN Japan",
    0x01e1: "NCS",
    0x01e2: "Human Entertainment",
    0x01e3: "Altron",
    0x01e4: "Jaleco",
    0x01e5: "Gaps Inc.",
    0x01eb: "Elf",
    0x01f8: "Jaleco",
    0x01fa: "Yutaka",
    0x01fb: "Varie",
    0x01fc: "T&ESoft",
    0x01fd: "Epoch Co., Ltd.",
    0x01ff: "Athena",
    0x0200: "Asmik",
    0x0201: "Natsume",
    0x0202: "King Records",
    0x0203: "Atlus",
    0x0204: "Epic/Sony Records (Japan)",
    0x0206: "IGS (Information Global Service)",
    0x0208: "Chatnoir",
    0x0209: "Right Stuff",
    0x020b: "NTT COMWARE",
    0x020d: "Spike",
    0x020e: "Konami Computer Entertainment Tokyo",
    0x020f: "Alphadream Corp.",
    0x0211: "Sting",
    0x021c: "A Wave",
    0x021d: "Motown Software",
    0x021e: "Left Field Entertainment",
    0x021f: "Extreme Entertainment Group",
    0x0220: "TecMagik",
    0x0225: "Cybersoft",
    0x0227: "Psygnosis",
    0x022a: "Davidson/Western Tech.",
    0x022b: "Unlicensed",
    0x0230: "The Game Factory Europe",
    0x0231: "Hip Games",
    0x0232: "Aspyr",
    0x0235: "Mastiff",
    0x0236: "iQue",
    0x0237: "Digital Tainment Pool",
    0x0238: "XS Games",
    0x0239: "Daiwon",
    0x0241: "PCCW Japan",
    0x0244: "KiKi Co. Ltd.",
    0x0245: "Open Sesame Inc.",
    0x0246: "Sims",
    0x0247: "Broccoli",
    0x0248: "Avex",
    0x0249: "D3 Publisher",
    0x024b: "Konami Computer Entertainment Japan",
    0x024d: "Square-Enix",
    0x024e: "KSG",
    0x024f: "Micott & Basara Inc.",
    0x0251: "Orbital Media",
    0x0262: "The Game Factory USA",
    0x0265: "Treasure",
    0x0266: "Aruze",
    0x0267: "Ertain",
    0x0268: "SNK Playmore",
    0x0299: "Yojigen",
}
