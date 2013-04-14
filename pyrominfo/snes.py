# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

from rominfo import RomInfoParser

class SNESParser(RomInfoParser):
    """
    Parse a SNES image. Valid extensions are smc, swc (TODO).
    SNES header references and related source code:
    * http://romhack.wikia.com/wiki/SNES_header
    * http://softpixel.com/~cwright/sianse/docs/Snesrom.txt
    * snescart.c of the MAME project:
    * http://mamedev.org/source/src/mess/machine/snescart.c.html
    """

    # Enum values
    SNES_MODE_20   = 20
    SNES_MODE_21   = 21
    SNES_MODE_22   = 22
    SNES_MODE_25   = 25
    SNES_MODE_ST   = "ST"
    SNES_MODE_BSX  = "BSX"
    SNES_MODE_BSLO = "BSLO"
    SNES_MODE_BSHI = "BSHI"

    def getValidExtensions(self):
        return ["smc", "swc"]

    def parse(self, filename):
        props = {}
        try:
            with open(filename, "rb") as f:
                data = bytearray(f.read())
                if data:
                    # Check for a header (512 bytes), and skip it if found
                    romOffset = 512 if self.hasSWCHeader(data) else 0
    
                    # First, look if the cart is HiROM or LoROM
                    headerOffset = self.findHiLoMode(data, romOffset)
    
                    # Then, detect BS-X carts
                    # Detect presence of BS-X Flash Cart
                    if  ROM[int_header_offs + 0x13] == 0x00 || ROM[int_header_offs + 0x13] == 0xff) &&
                    ROM[int_header_offs + 0x14] == 0x00)
                
                
                
        except IOError:
            pass
        return props

    def hasSWCHeader(self, data):
        """
        Check for a 512-byte SWC header prepended to the beginning of the file.
        """
        if len(data) >= 512:
            if data[8] == 0xaa and data[9] == 0xbb and data[10] == 0x04:
                # Found an SWC identifier
                return True
            if ((data[1] << 8) | data[0]) == (len(data) - 512) >> 13:
                # Some headers have the rom size at the start, if this matches with
                # the actual rom size, we probably have a header
                return True
            if len(data) % 0x8000 == 512:
                # As a last check we'll see if there's exactly 512 bytes extra to this image
                return True
        return False

    def findHiLoMode(self, buffer, offset):
        """
        This determines if a cart is in Mode 20, 21, 22 or 25; sets state->m_cart[0].mode
        and state->m_cart[0].sram accordingly; and returns the offset of the internal
        header (needed to detect BSX and ST carts).
        """
        # Now to determine if this is a lo-ROM, a hi-ROM or an extended lo/hi-ROM
        valid_mode20 = self.validate_infoblock(buffer, 0x007fc0)
        valid_mode21 = self.validate_infoblock(buffer, 0x00ffc0)
        valid_mode25 = self.validate_infoblock(buffer, 0x40ffc0)

        # Images larger than 32mbits are likely ExHiRom
        if valid_mode25:
            valid_mode25 += 4

        if valid_mode20 >= valid_mode21 and valid_mode20 >= valid_mode25:
            if buffer[0x007fd5] == 0x32 or len(buffer) - offset > 0x401000:
                mode = SNESParser.SNES_MODE_22 # ExLoRom (cart id = 0)
            else:
                mode = SNESParser.SNES_MODE_20 # LoRom (cart id = 0)

            retvalue = 0x007fc0

            # A few games require 512k, however we store twice as much to be
            # sure to cover the various mirrors.
            sram_max = 0x100000 # (cart id = 0)

        elif valid_mode21 >= valid_mode25:
            mode = SNESParser.SNES_MODE_21 # HiRom (cart id = 0)
            retvalue = 0x00ffc0
            sram_max = 0x20000 # (cart id = 0)

        else:
            mode = SNESParser.SNES_MODE_25 # ExHiRom (cart id = 0)
            retvalue = 0x40ffc0
            sram_max = 0x20000 # (cart id = 0)

        return retvalue

    def validate_infoblock(self, infoblock, offset):
        """
        This function assign a 'score' to data immediately after 'offset' to
        measure how valid they are as information block (to decide if the image
        is HiRom, LoRom, ExLoRom or ExHiRom).
        Code from bsnes, courtesy of byuu. <http://byuu.cinnamonpirate.com>
        """
        score = 0
        reset_vector = infoblock[offset + 0x3c] | (infoblock[offset + 0x3d] << 8)
        checksum     = infoblock[offset + 0x1e] | (infoblock[offset + 0x1f] << 8)
        ichecksum    = infoblock[offset + 0x1c] | (infoblock[offset + 0x1d] << 8)
        reset_opcode = infoblock[(offset & 0xFFFF8000) | (reset_vector & 0x7fff)] # first opcode executed upon reset
        mapper       = infoblock[offset + 0x15] & 0xef

        # $00:[000-7fff] contains uninitialized RAM and MMIO
        # reset vector must point to ROM at $00:[8000-ffff] to be considered valid
        if reset_vector < 0x8000:
            return 0

        # Some images duplicate the header in multiple locations, and others
        # have completely invalid header information that cannot be relied upon.
        # The code below will analyze the first opcode executed at the specified
        # reset vector to determine the probability that this is the correct
        # header. Score is assigned accordingly.

        # Most likely opcodes
        if reset_opcode in [0x78, 0x18, 0x38, 0x9c, 0x4c, 0x5c]:
            score += 8

        # Plausible opcodes
        if reset_opcode in [0xc2, 0xe2, 0xad, 0xae, 0xac, 0xaf, 0xa9, 0xa2, 0xa0, 0x20, 0x22]:
            score += 4

        # Implausible opcodes
        if reset_opcode in [0x40, 0x60, 0x6b, 0xcd, 0xec, 0xcc]:
            score -= 4

        # Least likely opcodes
        if reset_opcode in [0x00, 0x02, 0xdb, 0x42, 0xff]:
            score -= 8

        # Sometimes, both the header and reset vector's first opcode will match...
        # fallback and rely on info validity in these cases to determine the more
        # likely header. A valid checksum is the biggest indicator of a valid header.
        if checksum + ichecksum == 0xffff and checksum != 0 and ichecksum != 0:
            score += 4

        # Then there are the expected mapper values
        if offset == 0x007fc0 and mapper == 0x20: # 0x20 is usually LoROM
            score += 2
        if offset == 0x00ffc0 and mapper == 0x21: # 0x21 is usually HiROM
            score += 2
        if offset == 0x007fc0 and mapper == 0x22: # 0x22 is usually ExLoROM
            score += 2
        if offset == 0x40ffc0 and mapper == 0x25: # 0x25 is usually ExHiROM
            score += 2

        # Finally, there are valid values in the Company, Region etc. fields
        if infoblock[offset + 0x1a] == 0x33: # Company field: 0x33 indicates extended header
            score += 2;
        if infoblock[offset + 0x16] < 0x08: # ROM Type field
            score += 1
        if infoblock[offset + 0x17] < 0x10: # ROM Size field
            score += 1
        if infoblock[offset + 0x18] < 0x08: # SRAM Size field
            score += 1
        if infoblock[offset + 0x19] < 14: # Region field
            score += 1

        # Do we still have a positive score?
        if score < 0:
            score = 0

        return score



RomInfoParser.registerParser(SNESParser())


snes_publishers = {
    0x0000: "Unlicensed",
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
