# Copyright (C) 2013 Garrett Brown
# See Copyright Notice in rominfo.py

from rominfo import RomInfoParser

class GameboyParser(RomInfoParser):
    """
    Parse a Nintendo Gameboy image. Valid extensions are gb, gbc, cgb, sgb.
    Gameboy header references and related source code:
    * http://gbdev.gg8.se/wiki/articles/The_Cartridge_Header
    * http://gameboy.mongenel.com/dmg/asmmemmap.html
    * RomInfo.cpp of the VBA-M project:
    * http://vbam.svn.sourceforge.net/viewvc/vbam/trunk/src/win32/RomInfo.cpp?view=markup
    """

    def getValidExtensions(self):
        return ["gb", "gbc", "cgb", "sgb"]

    def parse(self, filename):
        props = {}
        with open(filename, "rb") as f:
            data = bytearray(f.read(0x150))
            if self.isValidData(data):
                props = self.parseBuffer(data)
        return props

    def isValidData(self, data):
        """
        The watermark we use here is the Nintendo logo. The Nintendo logo that is
        displayed when the gameboy gets turned on is stored in the 48 bytes from
        address $0104 to $0133. The hex dump is below. The gameboy boot procedure
        verifies the content of this bitmap and LOCKS ITSELF UP if these bytes are
        incorrect. As the logo is a registered trademark of Nintendo, this strategy
        was aimed at preventing unauthorized developers from publishing games for
        the handheld. However, a legal precedent was set in the United States in a
        case of Sega vs. Accolade (c.1993). Accolade published games for Sega's
        Genesis console containing a signature whose copyright was property of
        Sega. Accolade used this logo so that their games, which were not approved
        by Sega, would be able to play on the Genesis console. The judge ruled in
        favor of Accolade, stating that using a logo in this form was an anti-
        competitive practice, and therefore, Accolade was allowed to continue
        selling their games. Evil, twisted use of our copyright system, right?
            Source:
            http://gbdev.gg8.se/wiki/articles/The_Cartridge_Header
            http://gameboy.mongenel.com/dmg/asmmemmap.html
        Color Gameboy verifies only the first 24 bytes of the bitmap, but others
        (for example a pocket gameboy) verify all 48 bytes.
        """
        nintendo_logo = [
            0xCE, 0xED, 0x66, 0x66, 0xCC, 0x0D, 0x00, 0x0B, 0x03, 0x73, 0x00, 0x83, 0x00, 0x0C, 0x00, 0x0D,
            0x00, 0x08, 0x11, 0x1F, 0x88, 0x89, 0x00, 0x0E, 0xDC, 0xCC, 0x6E, 0xE6, 0xDD, 0xDD, 0xD9, 0x99,
            0xBB, 0xBB, 0x67, 0x63, 0x6E, 0x0E, 0xEC, 0xCC, 0xDD, 0xDC, 0x99, 0x9F, 0xBB, 0xB9, 0x33, 0x3E,
        ]
        return [b for b in data[0x104 : 0x104 + len(nintendo_logo)]] == nintendo_logo

    def parseBuffer(self, data):
        props = {}

        # 0134-0143 - Title, UPPER CASE ASCII
        props["title"] = self._sanitize(data[0x134 : 0x134 + 16])

        # 0143 - CGB Flag, in older cartridges this byte has been part of the Title
        #        but _sanitize() will strip non-ASCII values. Typical values are:
        #   80h: Game supports CGB functions, but works on old gameboys also
        #   C0h: Game works on CGB only (physically the same as 80h)
        # 0146 - SGB Flag, specifies whether the game supports SGB functions, common values are:
        #   00h: No SGB functions (Normal Gameboy or CGB only game)
        #   03h: Game supports SGB functions
        if data[0x143] & 0x80:
            props["platform"] = "Game Boy Color"
        elif data[0x146] == 0x03:
            props["platform"] = "Super Game Boy"
        else:
            props["platform"] = "Game Boy"
        props["sgb_support"] = "yes" if data[0x146] == 0x03 else ""

        # 0144-0145 - New Licensee Code, two character ASCII licensee code
        # 014B - Old Licensee Code in range 00-FF, value of 33h signals New License Code is used instead
        if data[0x14b] == 0x33:
            pub = data[0x144 : 0x144 + 2].decode("ascii", "ignore")
        else:
            pub = "%02X" % data[0x14b]
        props["publisher"] = gameboy_publishers.get(pub, "")
        props["publisher_code"] = pub

        # 0147 - Cartridge type, which Memory Bank Controller (if any) is used in the cartridge,
        #        and if further external hardware exists in the cartridge
        props["cartridge_type"] = gameboy_types.get(data[0x147], "")
        props["cartridge_type_code"] = "%02X" % data[0x147]

        # 0148 - ROM size of the cartridge
        props["rom_size"] = gameboy_rom_sizes.get(data[0x148], "")
        props["rom_size_code"] = "%02X" % data[0x148]

        # 0149 - Size of the external RAM in the cartridge (if any)
        props["ram_size"] = gameboy_ram_sizes.get(data[0x149], "")
        props["ram_size_code"] = "%02X" % data[0x149]

        # 014A - Destination code, if this version of the game is supposed to be sold in Japan.
        #        Only two values are defined: 00h - Japanese, 01h - Non-Japanese.
        props["destination"] = "Japan" if data[0x14a] == 0x00 else ""

        # 014C - Mask ROM version number of the game, usually 00h
        props["version"] = "%02X" % data[0x14c]

        # 014D - Header checksum, 8 bit checksum across the cartridge header bytes 0134-014C
        props["header_checksum"] = "%02X" % data[0x14d]

        # 014E-014F - Global checksum, 16 bit checksum across the whole cartridge ROM
        props["global_checksum"] = "%04X" % ((data[0x14e] << 8) | data[0x14f])

        return props

RomInfoParser.registerParser(GameboyParser())


gameboy_types = {
    0x00: "ROM",
    0x01: "ROM+MBC1",
    0x02: "ROM+MBC1+RAM",
    0x03: "ROM+MBC1+RAM+BATT",
    0x05: "ROM+MBC2",
    0x06: "ROM+MBC2+BATT",
    0x0b: "ROM+MMM01",
    0x0c: "ROM+MMM01+RAM",
    0x0d: "ROM+MMM01+RAM+BATT",
    0x0f: "ROM+MBC3+TIMER+BATT",
    0x10: "ROM+MBC3+TIMER+RAM+BATT",
    0x11: "ROM+MBC3",
    0x12: "ROM+MBC3+RAM",
    0x13: "ROM+MBC3+RAM+BATT",
    0x19: "ROM+MBC5",
    0x1a: "ROM+MBC5+RAM",
    0x1b: "ROM+MBC5+RAM+BATT",
    0x1c: "ROM+MBC5+RUMBLE",
    0x1d: "ROM+MBC5+RUMBLE+RAM",
    0x1e: "ROM+MBC5+RUMBLE+RAM+BATT",
    0x22: "ROM+MBC7+BATT",
    0x55: "GameGenie",
    0x56: "GameShark V3.0",
    0xfc: "ROM+POCKET CAMERA",
    0xfd: "ROM+BANDAI TAMA5",
    0xfe: "ROM+HuC-3",
    0xff: "ROM+HuC-1",
}

gameboy_rom_sizes = {
    0: "32KB",
    1: "64KB",
    2: "128KB",
    3: "256KB",
    4: "512KB",
    5: "1MB",
    6: "2MB",
    7: "4MB",
}

gameboy_ram_sizes = {
    0: "0KB",
    1: "2KB",
    2: "8KB",
    3: "32KB",
    4: "128KB",
    5: "64KB"
}

gameboy_publishers = {
    "01": "Nintendo",
    "02": "Rocket Games",
    "08": "Capcom",
    "09": "Hot B Co.",
    "0A": "Jaleco",
    "0B": "Coconuts Japan",
    "0C": "Coconuts Japan/G.X.Media",
    "0H": "Starfish",
    "0L": "Warashi Inc.",
    "0N": "Nowpro",
    "0P": "Game Village",
    "13": "Electronic Arts Japan",
    "18": "Hudson Soft Japan",
    "19": "S.C.P.",
    "1A": "Yonoman",
    "1G": "SMDE",
    "1P": "Creatures Inc.",
    "1Q": "TDK Deep Impresion",
    "20": "Destination Software",
    "22": "VR 1 Japan",
    "25": "San-X",
    "28": "Kemco Japan",
    "29": "Seta",
    "2H": "Ubisoft Japan",
    "2K": "NEC InterChannel",
    "2L": "Tam",
    "2M": "Jordan",
    "2N": "Smilesoft",
    "2Q": "Mediakite",
    "36": "Codemasters",
    "37": "GAGA Communications",
    "38": "Laguna",
    "39": "Telstar Fun and Games",
    "41": "Ubi Soft Entertainment",
    "42": "Sunsoft",
    "47": "Spectrum Holobyte",
    "49": "IREM",
    "4D": "Malibu Games",
    "4F": "Eidos/U.S. Gold",
    "4J": "Fox Interactive",
    "4K": "Time Warner Interactive",
    "4Q": "Disney",
    "4S": "Black Pearl",
    "4X": "GT Interactive",
    "4Y": "RARE",
    "4Z": "Crave Entertainment",
    "50": "Absolute Entertainment",
    "51": "Acclaim",
    "52": "Activision",
    "53": "American Sammy Corp.",
    "54": "Take 2 Interactive",
    "55": "Hi Tech",
    "56": "LJN LTD.",
    "58": "Mattel",
    "5A": "Mindscape/Red Orb Ent.",
    "5C": "Taxan",
    "5D": "Midway",
    "5F": "American Softworks",
    "5G": "Majesco Sales Inc",
    "5H": "3DO",
    "5K": "Hasbro",
    "5L": "NewKidCo",
    "5M": "Telegames",
    "5N": "Metro3D",
    "5P": "Vatical Entertainment",
    "5Q": "LEGO Media",
    "5S": "Xicat Interactive",
    "5T": "Cryo Interactive",
    "5W": "Red Storm Ent./BKN Ent.",
    "5X": "Microids",
    "5Z": "Conspiracy Entertainment Corp.",
    "60": "Titus Interactive Studios",
    "61": "Virgin Interactive",
    "62": "Maxis",
    "64": "LucasArts Entertainment",
    "67": "Ocean",
    "69": "Electronic Arts",
    "6E": "Elite Systems Ltd.",
    "6F": "Electro Brain",
    "6G": "The Learning Company",
    "6H": "BBC",
    "6J": "Software 2000",
    "6L": "BAM! Entertainment",
    "6M": "Studio 3",
    "6Q": "Classified Games",
    "6S": "TDK Mediactive",
    "6U": "DreamCatcher",
    "6V": "JoWood Productions",
    "6W": "SEGA",
    "6X": "Wannado Edition",
    "6Y": "LSP",
    "6Z": "ITE Media",
    "70": "Infogrames",
    "71": "Interplay",
    "72": "JVC Musical Industries Inc",
    "73": "Parker Brothers",
    "75": "SCI",
    "78": "THQ",
    "79": "Accolade",
    "7A": "Triffix Ent. Inc.",
    "7C": "Microprose Software",
    "7D": "Universal Interactive Studios",
    "7F": "Kemco",
    "7G": "Rage Software",
    "7H": "Encore",
    "7J": "Zoo",
    "7K": "BVM",
    "7L": "Simon & Schuster Interactive",
    "7M": "Asmik Ace Entertainment Inc./AIA",
    "7N": "Empire Interactive",
    "7Q": "Jester Interactive",
    "7T": "Scholastic",
    "7U": "Ignition Entertainment",
    "7W": "Stadlbauer",
    "80": "Misawa",
    "83": "LOZC",
    "8B": "Bulletproof Software",
    "8C": "Vic Tokai Inc.",
    "8J": "General Entertainment",
    "8N": "Success",
    "8P": "SEGA Japan",
    "91": "Chun Soft",
    "92": "Video System",
    "93": "BEC",
    "96": "Yonezawa/S'pal",
    "97": "Kaneko",
    "99": "Victor Interactive Software",
    "9A": "Nichibutsu/Nihon Bussan",
    "9B": "Tecmo",
    "9C": "Imagineer",
    "9F": "Nova",
    "9H": "Bottom Up",
    "9L": "Hasbro Japan",
    "9N": "Marvelous Entertainment",
    "9P": "Keynet Inc.",
    "9Q": "Hands-On Entertainment",
    "A0": "Telenet",
    "A1": "Hori",
    "A4": "Konami",
    "A6": "Kawada",
    "A7": "Takara",
    "A9": "Technos Japan Corp.",
    "AA": "JVC",
    "AC": "Toei Animation",
    "AD": "Toho",
    "AF": "Namco",
    "AG": "Media Rings Corporation",
    "AH": "J-Wing",
    "AK": "KID",
    "AL": "MediaFactory",
    "AP": "Infogrames Hudson",
    "AQ": "Kiratto. Ludic Inc",
    "B0": "Acclaim Japan",
    "B1": "ASCII",
    "B2": "Bandai",
    "B4": "Enix",
    "B6": "HAL Laboratory",
    "B7": "SNK",
    "B9": "Pony Canyon Hanbai",
    "BA": "Culture Brain",
    "BB": "Sunsoft",
    "BD": "Sony Imagesoft",
    "BF": "Sammy",
    "BG": "Magical",
    "BJ": "Compile",
    "BL": "MTO Inc.",
    "BN": "Sunrise Interactive",
    "BP": "Global A Entertainment",
    "BQ": "Fuuki",
    "C0": "Taito",
    "C2": "Kemco",
    "C3": "Square Soft",
    "C5": "Data East",
    "C6": "Tonkin House",
    "C8": "Koei",
    "CA": "Konami/Palcom/Ultra",
    "CB": "Vapinc/NTVIC",
    "CC": "Use Co.,Ltd.",
    "CD": "Meldac",
    "CE": "FCI/Pony Canyon",
    "CF": "Angel",
    "CM": "Konami Computer Entertainment Osaka",
    "CP": "Enterbrain",
    "D1": "Sofel",
    "D2": "Quest",
    "D3": "Sigma Enterprises",
    "D4": "Ask Kodansa",
    "D6": "Naxat",
    "D7": "Copya System",
    "D9": "Banpresto",
    "DA": "TOMY",
    "DB": "LJN Japan",
    "DD": "NCS",
    "DF": "Altron Corporation",
    "DH": "Gaps Inc.",
    "DN": "ELF",
    "E2": "Yutaka",
    "E3": "Varie",
    "E5": "Epoch",
    "E7": "Athena",
    "E8": "Asmik Ace Entertainment Inc.",
    "E9": "Natsume",
    "EA": "King Records",
    "EB": "Atlus",
    "EC": "Epic/Sony Records",
    "EE": "IGS",
    "EL": "Spike",
    "EM": "Konami Computer Entertainment Tokyo",
    "EN": "Alphadream Corporation",
    "F0": "A Wave",
    "G1": "PCCW",
    "G4": "KiKi Co Ltd",
    "G5": "Open Sesame Inc.",
    "G6": "Sims",
    "G7": "Broccoli",
    "G8": "Avex",
    "G9": "D3 Publisher",
    "GB": "Konami Computer Entertainment Japan",
    "GD": "Square-Enix",
    "HY": "Sachen",
}
