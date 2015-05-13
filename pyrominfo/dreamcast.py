# Copyright (C) 2015 Jan Holthuis
# See Copyright Notice in rominfo.py

import os
import csv
import struct
import time
import datetime
from rominfo import RomInfoParser


class DreamcastParser(RomInfoParser):
    """
    Parse a Dreamcast image. Valid extensions is cdi (little endian byte
    order), although gdi support is desired, too. This parser is derived from:
    * https://gist.github.com/Holzhaus/ae3dacf6a2e83dd00421
    Other related documentation and source code:
    * GD-ROM Format Basic Specifications Ver. 2.14 by Sega Enterprises, Ltd.
    * http://thekickback.com/dreamcast/GD-ROM%20Format%20Basic%20Specifications%20v2.14.pdf
    * Image reader code of the reicast-emulator project:
    * https://github.com/reicast/reicast-emulator/tree/master/core/imgread
    * IP0000.BIN documentation:
    * https://www.dropbox.com/s/ithnw69wy3ciuzn/IP0000.BIN.txt
    """

    def getValidExtensions(self):
        # TODO: Improve cdi support
        # TODO: Add chd support
        return ["cdi", "gdi"]

    def parse(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        data = None
        if ext == '.cdi':
            data = self._parse_cdi(filename)
        elif ext == '.gdi':
            data = self._parse_gdi(filename)
        else:
            print("Unknown image format")

        if data is None:
            return {}
        else:
            return self.parseBuffer(data)

    def _parse_cdi(self, filename):
        file_size = os.path.getsize(filename)
        if file_size < 8:
            print("Image size too short")
            return None

        with open(filename, mode="rb") as f:
            f.seek(file_size-8)
            image_version = struct.unpack("<I", f.read(4))[0]
            image_header_offset = struct.unpack("<I", f.read(4))[0]

            if image_header_offset == 0:
                print("Bad image format")
                return None

            if image_version not in (CDI_V2, CDI_V3, CDI_V35):
                print("Unsupported CDI version!")
                return None

            f.seek(image_header_offset)
            num_sessions = struct.unpack("<H", f.read(2))[0]

            last_data_track_info = (None, None)
            track_offset = 0
            for s in range(num_sessions):
                num_tracks = struct.unpack("<H", f.read(2))[0]

                for t in range(num_tracks):
                    temp_value = struct.unpack("<I", f.read(4))[0]
                    if temp_value != 0:
                        # extra data (DJ 3.00.780 and up)
                        f.seek(8, 1)

                    current_start_mark = struct.unpack("<10B", f.read(10))
                    if current_start_mark != cdi_track_start_mark:
                        print("Unsupported format: Missing track start mark")
                        return None

                    current_start_mark = struct.unpack("<10B", f.read(10))
                    if current_start_mark != cdi_track_start_mark:
                        print("Unsupported format: Missing track start mark")
                        return None

                    f.seek(4, 1)
                    filename_length = struct.unpack("<B", f.read(1))[0]
                    filename = f.read(filename_length).decode('utf-8')

                    f.seek(11, 1)
                    f.seek(4, 1)
                    f.seek(4, 1)
                    temp_value = struct.unpack("<I", f.read(4))[0]
                    if temp_value == 0x80000000:
                        # DiscJuggler 4
                        f.seek(8, 1)
                    f.seek(2, 1)
                    track_pregap_length = struct.unpack("<I", f.read(4))[0]
                    track_length = struct.unpack("<I", f.read(4))[0]
                    f.seek(6, 1)
                    track_mode = struct.unpack("<I", f.read(4))[0]
                    f.seek(12, 1)
                    track_start_lba = struct.unpack("<I", f.read(4))[0]
                    track_total_length = struct.unpack("<I", f.read(4))[0]
                    f.seek(16, 1)
                    sector_size_id = struct.unpack("<I", f.read(4))[0]

                    if sector_size_id not in cdi_track_sector_sizes:
                        print("Unsupported sector size")
                        return
                    track_sector_size = cdi_track_sector_sizes[sector_size_id]

                    if track_mode not in cdi_track_modes:
                        print("Unsupported format: Track mode not supported")
                    elif track_mode > 0:
                        track_position = (track_offset + track_pregap_length *
                                          track_sector_size)
                        last_data_track_info = (track_position,
                                                track_sector_size)

                    track_offset += track_total_length * track_sector_size

                    f.seek(29, 1)
                    if image_version != CDI_V2:
                        f.seek(5, 1)
                        temp_value = struct.unpack("<I", f.read(4))[0]
                        if temp_value == 0xffffffff:
                            # extra data (DJ 3.00.780 and up)
                            f.seek(78, 1)

                # Skip to next session
                f.seek(4, 1)
                f.seek(8, 1)
                if image_version != CDI_V2:
                    f.seek(1, 1)

            # Extract IP.BIN data
            if last_data_track_info == (None, None):
                print("Unsupported Image: Data track not found")
                return

            ip_bin_position = last_data_track_info[0]
            if last_data_track_info[1] == 2336:
                ip_bin_position += 8
            f.seek(ip_bin_position)
            data = f.read(256)

            return data

    def _parse_gdi(self, filename):
        with open(filename, mode="r") as f:
            num_tracks = int(f.readline().strip())
            if num_tracks < 3:
                print("GDI images should have at least 3 tracks!")
            gdi_reader = csv.reader(f, delimiter=' ', quotechar='"')
            for row in gdi_reader:
                track_index = int(row[0])
                track_ctrl = int(row[2])
                track_mode = 0 if track_ctrl == 0 else 1
                track_filename = os.path.abspath(os.path.join(
                    os.path.dirname(filename), row[4]))
                if track_index == 3:
                    break
        if track_index == 3:
            if track_mode == 0:
                print("Track 3 should be a data track, but it isn't!")
            else:
                # Extract IP.BIN data
                with open(track_filename, mode="rb") as f:
                    ip_bin_position = 0x10
                    f.seek(ip_bin_position)
                    return f.read(256)

    def parseBuffer(self, data):
        # See SEGA's GD-ROM Format Basic Specifications Ver. 2.13, p. 13 for
        # details.
        fmt = "<16s16s5s11s8s8s10s6s8s8x12s4x16s96s32x"
        try:
            ip_info = (s.decode('ascii').strip() for s in
                       struct.unpack(fmt, data))
        except (struct.error, UnicodeDecodeError):
            return {}
        keys = ('hardware_id',
                'hardware_vendor_id',
                'media_id',
                'media_info_code',
                'region_code',
                'compatible_peripherals_code',
                'product_id',
                'product_version',
                'release_date_code',
                'bootfile',
                'publisher',
                'game_title')

        props = dict(zip(keys, ip_info))
        try:
            peripherals_code = int(props['compatible_peripherals_code'], 16)
            peripherals = []
            for p_code, p_desc in dc_peripherals.items():
                if peripherals_code & p_code == p_code:
                    peripherals.append(p_desc)
            props['compatible_peripherals'] = tuple(peripherals)
            props['media_info'] = tuple(
                int(x) for x in props['media_info_code'][6:].split('/'))
            props['release_date'] = datetime.date(
                *time.strptime(props['release_date_code'], "%Y%m%d")[:3])
            props['regions'] = tuple(
                dc_regions.get(r) for r in props['region_code'])
        except (KeyError, IndexError, ValueError):
            return {}
        return props


RomInfoParser.registerParser(DreamcastParser())

CDI_V2 = 0x80000004
CDI_V3 = 0x80000005
CDI_V35 = 0x80000006

cdi_track_start_mark = (0, 0, 0x01, 0, 0, 0, 0xFF, 0xFF, 0xFF, 0xFF)
cdi_track_sector_sizes = {
    0: 2048,
    1: 2336,
    2: 2352
}
cdi_track_modes = {
    0: 'audio',
    1: 'mode1',
    2: 'mode2'
}

dc_regions = {
    'J': 'Asia',     # Japan, Korea, Asian NTSC
    'U': 'America',  # North American NTSC, Brazilian PAL-M, Argentine PAL-N
    'E': 'Europe'    # European PAL
}

dc_peripherals = {
    0b0000000000000000000000000001: 'Uses Windows CE',
    0b0000000000000000000000010000: 'VGA box support',
    # Expansion units
    0b0000000000000000000100000000: 'Other expansions',
    0b0000000000000000001000000000: 'Puru Puru pack',
    0b0000000000000000010000000000: 'Mike device',
    0b0000000000000000100000000000: 'Memory card',
    # Required peripherals
    0b0000000000000001000000000000: 'Start/A/B/Directions',
    0b0000000000000010000000000000: 'C button',
    0b0000000000000100000000000000: 'D button',
    0b0000000000001000000000000000: 'X button',
    0b0000000000010000000000000000: 'Y button',
    0b0000000000100000000000000000: 'Z button',
    0b0000000001000000000000000000: 'Expanded direction buttons',
    0b0000000010000000000000000000: 'Analog R trigger',
    0b0000000100000000000000000000: 'Analog L trigger',
    0b0000001000000000000000000000: 'Analog horizontal controller',
    0b0000010000000000000000000000: 'Analog vertical controller',
    0b0000100000000000000000000000: 'Expanded analog horizontal',
    0b0001000000000000000000000000: 'Expanded analog vertical',
    # Optional peripherals
    0b0010000000000000000000000000: 'Gun',
    0b0100000000000000000000000000: 'Keyboard',
    0b1000000000000000000000000000: 'Mouse'
}
