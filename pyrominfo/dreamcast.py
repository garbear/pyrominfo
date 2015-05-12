# Copyright (C) 2015 Jan Holthuis
# See Copyright Notice in rominfo.py

import os
import struct
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
    """

    def getValidExtensions(self):
        # TODO: Improve cdi support
        # TODO: Add gdi support
        return ["cdi"]

    def parse(self, filename):
        props = {}
        file_size = os.path.getsize(filename)
        if file_size < 8:
            print("Image size too short")
            return props

        with open(filename, mode="rb") as f:
            f.seek(file_size-8)
            image_version = struct.unpack("<I", f.read(4))[0]
            image_header_offset = struct.unpack("<I", f.read(4))[0]

            if image_header_offset == 0:
                print("Bad image format")
                return props

            if image_version not in (CDI_V2, CDI_V3, CDI_V35):
                print("Unsupported CDI version!")
                return props

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
                        return props

                    current_start_mark = struct.unpack("<10B", f.read(10))
                    if current_start_mark != cdi_track_start_mark:
                        print("Unsupported format: Missing track start mark")
                        return props

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

            props = self.parseBuffer(data)
            return props

    def parseBuffer(self, data):
        try:
            ip_info = (s.decode('ascii').strip() for s in
                       struct.unpack("<16s16s16s8s8s10s6s16s16s16s128s", data))
        except (struct.error, UnicodeDecodeError):
            return {}
        keys = ('hardware_id', 'maker_id', 'disc_id', 'areas', 'peripherals',
                'product_id', 'product_version', 'release_date', 'bootfile',
                'publisher', 'product_name')

        return dict(zip(keys, ip_info))


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