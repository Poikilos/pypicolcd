#!/bin/env python3
# pypicolcd, a module for driverless writing to picoLCD
# Copyright (C) 2018  Jake Gustafson

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

about_msg = """
pypicolcd  Copyright (C) 2018  Jake Gustafson
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions; open LICENSE file in text editor for details.
"""

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
        index = ids[-1]  # -1 gets top (last) graphics instruction
        color = canvas.itemcget(index, "fill")
        color = color.upper()
        if color != '':
            return color.upper()
    else:
        print("[ picolcd.py ] WARNING in get_pixel_color: no color"
              " at " + str((x, y)))
    return "WHITE"

def get_pixels_2d_of(canvas):
    width = int(canvas["width"])
    height = int(canvas["height"])
    colors = []
    for y in range(height):
        row = []
        for x in range(width):
            row.append(get_pixel_color(canvas, x, y))
        colors.append(row)
    return colors

def get_pixels_1d_of(canvas):
    width = int(canvas["width"])
    height = int(canvas["height"])
    colors = []
    for y in range(height):
        for x in range(width):
            colors.append(get_pixel_color(canvas, x, y))
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


    # row,col: the y,x location (in that order; though if
    # picolcd.dc["type"] is graphics, it will be a pixel location
    # where row is the middle of the letters)
    def draw_text(self, row, col, text, font=None):
        if self.dc["type"] == "graphics":
            start_y = row
            start_x = col
            # print("[ picolcd ] ERROR in draw_text:"
                  # " bitmap font, required for draw_text in "
                  # " graphics model type, is not yet implemented")
            canvas = tk.Canvas(width=self.dc["width"], height=self.dc["height"])
            bg_id = canvas.create_rectangle(0, 0, self.dc["width"],
                                            self.dc["height"],
                                            fill="WHITE")
            text_id = None
            black_count = 0
            unknowns = []
            if font is not None:
                text_id = canvas.create_text(
                    start_x, start_y, anchor=tk.W,
                    fill="BLACK", # fill="#000"
                    text=text,
                    font=font)
            else:
                text_id = canvas.create_text(
                    start_x, start_y, anchor=tk.W,
                    fill="BLACK",
                    text=text)
            on_count = 0
            # pixels = get_pixels_1d_of(canvas)
            # for p_i in range(len(pixels)):
                # pixel = pixels[p_i]
                # if pixel == "BLACK":
                    # y = int(p_i / self.dc["width"])
                    # x = int(p_i % self.dc["width"])
                    # self.set_pixel(x, y, True, refresh_enable=False)
                # elif pixel == "WHITE":
                    # pass
                # else:
                    # if pixel not in unknowns:
                        # unknowns.append(pixel)
            rows = get_pixels_2d_of(canvas)
            y = 0
            for row in rows:
                x = 0
                for pixel in row:
                    if pixel == "BLACK":
                        on_count += 1
                        self.set_pixel(x, y, True, refresh_enable=False)
                    elif pixel == "WHITE":
                        pass
                    else:
                        if pixel not in unknowns:
                            unknowns.append(pixel)
                    x += 1
                y += 1

            if len(unknowns) > 0:
                print("[ PicoLcd ] WARNING in draw_text: offscreen"
                      " surface had unknown pixels: "
                      + str(unknowns))
            # for y in range(self.dc["height"]):
                # for x in range(start_x, self.dc["width"]):
            if on_count < 1:
                print("[ PicoLcd ] WARNING in draw_text: offscreen"
                      + " buffer had only " + str(on_count)
                      + " text pixels")

            self.refresh()
            return 0
        else:
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
    # where invalidated (where set_pixel was called or other operation
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

    # Set a one-bit pixel to the value of on (invalidate block if
    #   pixel differs from framebuffer or force_refresh_enable is True).
    # on: determines whether to turn the pixel on or off
    # refresh_enable: draw the affected block from framebuffers
    #   (if False, you will have to call refresh later (which will draw
    #   all invalidated blocks automatically)
    # force_refresh_enable: draw even if does not differ
    #   from framebuffer
    def set_pixel(self, x, y, on, refresh_enable=True, force_refresh_enable=False):
        # NOTE: one byte covers 8 pixels on y axis from landscape view
        if force_refresh_enable:
            refresh_enable=True
        zone_width = self.dc["width"] / self.dc["zones"]
        zone_i = int(x/zone_width)
        block_i = int(y/self.dc["blockrows"])
        bs = self.dc["block_size"]
        fb_i = block_i * self.dc["zones"] + zone_i
        bit_i = y % self.dc["ppb"]
        byte_i = x % self.dc["block_size"]
        pixel = 1 << bit_i
        # if self.verbose_enable:
            # print("[ PicoLcd ] (verbose message in set_pixel)"
                  # + " " + str((x,y)) + " results in"
                  # + " framebuffer[" + str((fb_i)) + "]"
                  # + " zone,block=" + str((zone_i, block_i))
                  # + " byte=" + str(byte_i) + " bit=" + str(bit_i))
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
                        self.change_enables[fb_i] = True
            else:
                if result & pixel > 0:
                    framebuffer[byte_i] ^= pixel
                    self.change_enables[fb_i] = True
                else:
                    if not force_refresh_enable:
                        refresh_enable = False
                    else:
                        self.change_enables[fb_i] = True
            if refresh_enable:
                # msg = "refreshing"
                # if not self.change_enables[fb_i]:
                    # msg = "not refreshing"
                # print(msg + " " + str((zone_i, block_i)))
                self.refresh_block(zone_i, block_i)
        else:
            print("[ PicoLcd ] ERROR in set_pixel: buffer "
                  + str(fb_i) + " does not exist in "
                  + str(len(self.framebuffers)) + "-len buffer list.")

    def clear(self):
        self.reset_framebuffer()
        self.invalidate()
        self.refresh()

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
