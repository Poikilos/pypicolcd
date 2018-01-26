#!/bin/env python3
try:
    import usb
except ImportError:
    print("pypicolcd requires pyusb")
    print("such as via:")
    print("  sudo pip install pyusb")

import time

try:
    import Tkinter as tk
    import tkFont
    import ttk
except ImportError:  # Python 3
    import tkinter as tk
    import tkinter.font as tkFont
    import tkinter.ttk as ttk


# TODO: root = tk.Tk()  # never shown, just for font rendering


def bytes(*b):
    return "".join([chr(x) for x in b])

OUT_REPORT_LED_STATE            = 0x81
OUT_REPORT_LCD_BACKLIGHT        = 0x91
OUT_REPORT_LCD_CONTRAST         = 0x92
OUT_REPORT_LCD_CONTROL          = 0x93
OUT_REPORT_LCD_CLEAR            = 0x94
OUT_REPORT_DATA                 = 0x95  # from official 128x64 driver
OUT_REPORT_CMD_DATA             = 0x96  # from official 128x64 driver
OUT_REPORT_LCD_TEXT             = 0x98  # only for text models
OUT_REPORT_LCD_FONT             = 0x9C  # only for text models
width = 20
height = 4 # can also be 2
ids = [ 0xc001, 0xc002 ]

DC_DICT = {}  # devices' characteristics dicts
this_dc = {}
this_dc["type"] = "text"
this_dc["name"] = "picoLCD 20x4"
this_dc["width"] = 20
this_dc["height"] = 4  # or 2, but that Product ID is unknown
this_dc["blockrows"] = 1
this_dc["zones"] = 1
this_dc["block_size"] = 80
# this_dc["chip_orientation"] = "landscape"
DC_DICT[0xc001] = this_dc
this_dc = {}
this_dc["type"] = "graphics"
this_dc["name"] = "picoLCD 256x64"
# this_dc["chip_orientation"] = "portrait"
this_dc["ppb"] = 8  # VERTICAL pixels per byte
this_dc["width"] = 256
this_dc["height"] = 64
this_dc["blockrows"] = 8
this_dc["zones"] = 8
this_dc["block_size"] = 32 # ok since 8x8x32 == 256*(64/8) == 2048
this_dc["inverted"] = 1  # 1 as per official driver
                         # /picoLCDGraphic/Configs/lcd4linux.conf
this_dc["chip_size"] = 64 * (64 / this_dc["ppb"])  # 64x64 pixels,
                                                   # but 1-bit
this_dc["chip_count"] = 4
DC_DICT[0xc002] = this_dc

def get_pixel_color(canvas, x, y):
    ids = canvas.find_overlapping(x, y, x, y)

    if len(ids) > 0:
        index = ids[-1]
        color = canvas.itemcget(index, "fill")
        color = color.upper()
        if color != '':
            return tk.Color[color.upper()]
    return "WHITE"

def get_pixels_of(canvas):
    width = int(canvas["width"])
    height = int(canvas["height"])
    colors = []

    for x in range(width):
        column = []
        for y in range(height):
            column.append(get_pixel_color(canvas, x, y))
        colors.append(column)
    return colors


class PicoLcd:

    def __init__(self):
        self.dc = None  # device characteristics
        self.framebuffer = None
        self.framebuffers = None
        self.change_enables = None
        self.handle = None
        self.verbose_enable = False
        buses = usb.busses()
        error = None
        for bus in buses:
            for device in bus.devices:
                if device.idVendor == 0x04d8 and \
                        device.idProduct in DC_DICT.keys():
                       # device.idProduct in ids:
                    lcd = device
                    self.dc = DC_DICT[device.idProduct]
                    print("[ picolcd ] (verbose message in __init__)"
                          " found " + self.dc["name"])
        if self.dc is not None:
            self.change_enables = []
            for block_i in range(self.dc["blockrows"]):
                for zone_i in range(self.dc["zones"]):
                    self.change_enables.append(False)
            if self.dc["type"] == "graphics":
                # block_count = self.dc["blockrows"] * self.dc["zones"]
                # self.framebuffers = []
                # for fb_i in range(block_count):
                    # self.framebuffer = [0] * (self.dc["block_size"])
                    # self.framebuffer[1] = 255
                    # if self.framebuffer[0] == 255:
                        # # deal with list initialization paranoia
                        # print("[ pycolcd ] ERROR: failed to create unique"
                              # " framebuffer elements")
                        # sys.exit(1)
                    # else:
                        # self.framebuffer[1] = 0
                        # self.framebuffers.append(self.framebuffer)
                pass
            else:
                # self.framebuffers = []
                # self.framebuffer = [0] * (self.dc["block_size"])
                # self.framebuffers.append(self.framebuffer)
                pass
            self.reset_framebuffer()
        if lcd is not None:
            self.handle = lcd.open()
            try:
                self.handle.detachKernelDriver(0)
            except usb.USBError:
                # print("[ picolcd ] nothing to detach")
                pass
            self.handle.claimInterface(0)
            self.handle.setAltInterface(0)
            # print("[ picolcd ] claimed interface 0")
        else:
            if error is None:
                error = ("ERROR in picolcd: Failed to find a known"
                         " product ID connected")
        if error is not None:
            print(error)

    def wr(self, m):
        # interruptWrite(endpoint, buffer, timeout)
        # returns bytes written
        return self.handle.interruptWrite(usb.ENDPOINT_OUT + 1, m, 1000)

    def reset_framebuffer(self):
        self.change_enables = []
        self.framebuffers = []
        # for block_i in range(self.dc["blockrows"]):
            # for zone_i in range(self.dc["zones"]):
                # self.change_enables.append(False)
        block_count = self.dc["blockrows"] * self.dc["zones"]
        for fb_i in range(block_count):
            self.change_enables.append(False)
            self.framebuffer = [0] * (self.dc["block_size"])
            self.framebuffer[1] = 255
            if self.framebuffer[0] == 255:
                # deal with list initialization paranoia
                print("[ pycolcd ] ERROR: failed to create unique"
                      " framebuffer elements")
                sys.exit(1)
            else:
                self.framebuffer[1] = 0
                self.framebuffers.append(self.framebuffer)



    def draw_text(self, row, col, text):
        if self.dc["type"] == "graphics":
            print("[ picolcd ] ERROR in draw_text:"
                  " bitmap font, required for draw_text in "
                  " graphics model type, is not yet implemented")
            return 0
        addr = {0: 0x80, 1: 0xc0, 2:0x94, 3:0xd4}[row] + col
        result = self.wr(bytes(0x94, 0x00, 0x01, 0x00, 0x64, addr))
        if result < 1:
            print("[ picolcd ] ERROR: " + str(result)
                  + "byte(s) written for address")
        self.wr(bytes(OUT_REPORT_DATA, 0x01, 0x00, 0x01, len(text))
                + text)

    # invalidate rectangle of lcd to force refresh to refresh them
    # next time refresh is called (if no params, then entire screen:
    # zones 0 to picolcd.dc["zones"]
    # and blocks 0 to picolcd.dc["blockrows"])
    # if you want a non-rectangle, set framebuffer numbers in
    # picolcd.change_enables manually
    def invalidate(self, zones=None, blocks=None):
        if zones is None:
            zones = []
            for i in range(self.dc["zones"]):
                zones.append(i)
        if blocks is None:
            blocks = []
            for i in range(self.dc["blockrows"]):
                blocks.append(i)
        # trim redundant calls to even zone (even zone always
        # must be drawn when odd zone is drawn anyway):
        for zone_i in reversed(zones):
            if (zone_i % 2 == 1) and ((zone_i - 1) in zones):
                del zones[zone_i - 1]
        for block_i in blocks:
            for zone_i in zones:
                fb_i = block_i * self.dc["zones"] + zone_i
                self.change_enables[fb_i] = True
                # self.refresh_block(zone_i, block_i)

    # Refresh all or part of lcd from framebuffers
    # where invalidated (where setpixel was called or other operation
    # was done). For advanced use, such as if you drew to a framebuffer
    # manually, call invalidate first to inform PicoLcd which
    # framebuffers changed
    def refresh(self):
        for fb_i in range(len(self.change_enables)):
            if self.change_enables[fb_i]:
                block_i = int(fb_i / self.dc["blockrows"])
                zone_i = fb_i % self.dc["blockrows"]
                self.refresh_block(zone_i, block_i)


    def refresh_block(self, zone_i, block_i):
        result = 0
        data_len = 32  # always 32 so you don't lose your place
                       # (positioning is relative when accessing
                       # an odd zone aka right side of a chip)
        cs = int(zone_i/2)
        chipsel = cs << 2
        # bs = self.dc["block_size"]
        cmd3 = [
            OUT_REPORT_CMD_DATA,
            chipsel,
            0x02,
            0x00,
            0x00,
            0xb8 | block_i,  # [5] 0xb8|line,
            0x00,
            0x00,
            0x40,
            0x00,
            0x00,
            data_len
        ]

        # if zone is odd, even zone must be filled first to get to it:
        if zone_i % 2 == 1:
            fb = self.framebuffers[block_i * self.dc["zones"] + (zone_i-1)]
            cmd3.extend(fb)
            result += self.wr(cmd3)
            cmd4 = [
                OUT_REPORT_DATA,
                chipsel | 0x01,
                0x00,
                0x00,
                data_len
            ]
            fb = self.framebuffers[block_i * self.dc["zones"] + zone_i]
            cmd4.extend(fb)
            result += self.wr(cmd4)
        else:
            fb = self.framebuffers[block_i * self.dc["zones"] + zone_i]
            cmd3.extend(fb)
            result += self.wr(cmd3)

    # refresh_enable: draw the affected block from framebuffers
    # force_refresh_enable: draw even if does not differ from current
    def setpixel(self, x, y, on, refresh_enable=True, force_refresh_enable=False):
        # NOTE: one byte covers 8 pixels on y axis from landscape view
        zone_width = self.dc["width"] / self.dc["zones"]
        zone_i = int(x/zone_width)
        block_i = int(y/self.dc["blockrows"])
        bs = self.dc["block_size"]
        fb_i = block_i * self.dc["zones"] + zone_i
        bit_i = y % self.dc["ppb"]
        byte_i = x % self.dc["block_size"]
        pixel = 1 << bit_i
        if self.verbose_enable:
            print("[ PicoLcd ] (verbose message in setpixel)"
                  + " " + str((x,y)) + " results in"
                  + " framebuffer[" + str((fb_i)) + "]"
                  + " zone,block=" + str((zone_i, block_i))
                  + " byte=" + str(byte_i) + " bit=" + str(bit_i))
        if fb_i < len(self.framebuffers):
            framebuffer = self.framebuffers[fb_i]
            result = framebuffer[byte_i]
            # TODO: account for "inverted" mode
            if on:
                if result | pixel != result:
                    framebuffer[byte_i] |= pixel
                    self.change_enables[fb_i] = True
                else:
                    if not force_refresh_enable:
                        refresh_enable = False
            else:
                if result & pixel > 0:
                    framebuffer[byte_i] ^= pixel
                    self.change_enables[fb_i] = True
                else:
                    if not force_refresh_enable:
                        refresh_enable = False
            if refresh_enable:
                self.refresh_block(zone_i, block_i)
        else:
            print("[ PicoLcd ] ERROR in setpixel: buffer "
                  + str(fb_i) + " does not exist in "
                  + str(len(self.framebuffers)) + "-len buffer list.")

    # enable: True is black, as False allows backlight to show through
    # this is very inaccurate, and not changed to match info in README yet
    def _pokepixel(self, x, y, enable, diff_enable=True):
        addr = None
        print("[ picolcd ] ERROR in _pokepixel: Nothing done since"
              " seems impossible (don't ever use _pokepixel)")
        return 0
        if self.dc["type"] == "text":
            print("[ picolcd ] ERROR in _pokepixel: not available in"
                  " text device type")
            return 0
        # see patched lcd4linux source on
        # http://www.linuxconsulting.ro/picoLCD/
        # * goto/write command is
        #   [0x98, y, x, len, rawdata]
        # 128, 192, 148, 212
        # addr = {0: 0x80, 1: 0xc0, 2:0x94, 3:0xd4}[y] + x
        data_len = 1
        data = 1 << (x%self.dc["ppb"])
        byte_x = int(x/self.dc["ppb"])  # since 1-bit graphics
        pitch = int(self.dc["width"] / self.dc["ppb"])
        byte_i = y * pitch + byte_x
        # NOTE: official driver uses whole byte of framebuffer as bool
        # but this code keeps actual copy of byte, where only bits are
        # on where the pixel is on as per the destination (1-bit) format
        dest_data = self.framebuffer[byte_i]
        cs = int(byte_i/self.dc["chip_size"])

        chipsel = cs << 2
        # chipsel | 0x01 clears bottom (landscape right) of chip
        # (only seems to work with relative positioning)
        # self.wr(bytes(OUT_REPORT_DATA, y, x, data_len, data))
        # if line is None:
        # line = int(x/8)
        chip_height_px = int(
            (self.dc["chip_size"] * self.dc["ppb"])
            / self.dc["width"]
        )
        local_y = y - (cs * chip_height_px)
        sidestep = int(x/self.dc["ppb"])
        halfchip_height = int(chip_height_px/2)
        chipside = int(round(y/halfchip_height))
        # for [5] there are 8 lines, so line b8|line could be:
        # |0, |1, |2, |3, |4, |5, |6, |7
        # b8, b9, ba, bb, bc, bd, be, bf
        # starting from top down in landscape view

        # chipsel (at [1]) is cs << 2 where cs is chip number 0-3
        # (in the short command it is |1)
        # 00, 04, 08, 0c (for long command)
        # |1, |1, |1, |1
        # 01, 05, 09, 0d (for short command)
        cmd3 = [
            OUT_REPORT_CMD_DATA,
            byte_i, # chipsel | chipside,  # this is a BYTE
            0x02,
            0x00,
            0x00,
            0x00, # [5] sidestep,  # 0xb8|sidestep,  # 0xb8|line,
            0x00,
            0x00,
            0x00,# 0x40,
            0x00,
            0x00,
            data_len
        ]

        cmd4 = [
            OUT_REPORT_DATA,
            chipsel | chipside,
            0x00,
            0x00,
            data_len
        ]
        cmd4_data_start = len(cmd4)
        # for index in range(data_len):
        if (not diff_enable) or ((data | dest_data) != dest_data):
            # result_data = data
            # if diff_enable:
            result_data = data
            # NOTE: official driver's frame buffer has OxFF
            # if pLG_framebuffer[y * 256 + x] ^ self.dc["inverted"]:
                # pixel |= (1 << bit);
            # representing one bit (eight times bigger than chip_size)
            # if self.framebuffer[byte_i) ^ self.dc["inverted"] > 0:
                # if differs from framebuffer
            result_data |= self.framebuffer[byte_i]
            self.framebuffer[byte_i] = result_data

            cmd3.append(result_data)
            cmd4.append(result_data)
            # self.wr(cmd3)
            self.wr(cmd4)

    def clear(self, val=0x00, data_len=32, line_len=8, chip_count=4):
        # self.framebuffer = [0] * (self.dc["width"] * self.dc["height"])
        self.reset_framebuffer()
        if self.dc["type"] == "text":
            for row in range(self.dc["height"]):  # formerly range(4)
                self.draw_text(row, 0, " " * self.dc["width"])  # formerly * 20
        else:  # self.dc["type"] == "graphics":
            addr_count = 0
            # print("[ picocld ] clearing pixels 2nd slowest way...")
            # for row in range(self.dc["height"]):
            # formerly range(4)
                # self.setpixel(row, 0, " " * self.dc["width"])
                # formerly * 20
            # see patched lcd4linux source at
            # http://www.linuxconsulting.ro/picoLCD/
            for cs in range(chip_count):
                chipsel = cs << 2
                for line in range(line_len):
                    # data = []
                    cmd3 = [
                        OUT_REPORT_CMD_DATA,
                        chipsel,
                        0x02,
                        0x00,
                        0x00,
                        0xb8|line,
                        0x00,
                        0x00,
                        0x40,
                        0x00,
                        0x00,
                        data_len
                    ]
                    cmd3_data_start = len(cmd3)
                    cmd4 = [
                        OUT_REPORT_DATA,
                        chipsel | 0x01,
                        0x00,
                        0x00,
                        data_len
                    ]
                    cmd4_data_start = len(cmd4)
                    for index in range(data_len):
                        # data.append(0x00)
                        # extend list for now--set to pixel later
                        cmd3.append(0x00)
                        cmd4.append(0x00)
                    SCREEN_H = self.dc["height"]
                    SCREEN_W = self.dc["width"]
                    # each cs handles 1 64x64 pixel memory chip
                    # each index paints 2 rows
                    # (memory is addressed from landscape perspective)
                    for index in range(data_len):
                        pixel = val
                        offset = cmd3_data_start + index

                        for bit in range(8):
                            x = cs * 64 + index;
                            y = (line * 8 + bit + 0) % SCREEN_H
                            # TODO (from official driver but seems
                            # wrong since XOR does not change left
                            # param bit if right param bit is zero):
                            # if self.framebuffer[y * 256 + x] ^ \
                                    # self.dc["inverted"] > 0:
                            pixel |= (1 << bit)
                        if val == 0x00:
                            cmd3[offset] = 0x00
                        else:
                            cmd3[offset] = pixel
                    for i in range(data_len):
                        index = i + 32
                        pixel = val
                        for bit in range(8):
                            x = cs * 64 + index;
                            y = (line * 8 + bit + 0) % SCREEN_H
                            # TODO (from official driver but seems
                            # wrong since XOR does not change left
                            # param bit if right param bit is zero):
                            # if self.framebuffer[y * 256 + x] ^ self.dc["inverted"]:
                            pixel |= (1 << bit)

                        if val == 0x00:
                            cmd4[cmd4_data_start + (index - 32)] = 0x00
                        else:
                            cmd4[cmd4_data_start + (index - 32)] = pixel
                        addr_count += 1
                    # clear top (landscape left) of this chip:
                    self.wr(cmd3)
                    # clear clear bottom (landscape right) of this chip:
                    self.wr(cmd4)
                # end for line
            # end for cs (chip index)
            print("[ picolcd ] cleared " + str(addr_count)
                  + " block(s)")
            pass

    def backlight(self, brightness):
        self.wr(bytes(OUT_REPORT_LCD_BACKLIGHT, brightness))

    def leds(self, state):
        self.wr(bytes(OUT_REPORT_LED_STATE, state))

    def flash(self):
        for brightness in list(range(20, 0, -1)) + list(range(0, 21)):
            self.backlight(brightness)
            time.sleep(.01)

if __name__ == "__main__":
    from datetime import datetime
    p = PicoLcd()
    p.clear()
    p.draw_text(0, 0, "It worked!")
    p.draw_text(3, 0, datetime.now().ctime()[:20])
    print("You can use this module like:")
    print("  from picolcd import PicoLcd")
    print("  p = PicoLcd()")
