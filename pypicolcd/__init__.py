#!/usr/bin/env python
"""
pypicolcd, a module for driverless writing to picoLCD
Copyright (C) 2018  Jake Gustafson

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import time
from datetime import datetime
import sys
import traceback
import os
import random
import inspect
from timeit import default_timer as best_timer
from PIL import Image, ImageDraw, ImageFont
# from PIL import Image, ImageDraw, ImageFont, ImageColor

try:
    import usb
except ImportError:
    # NOTE: ModuleNotFoundError is only available in Python 3.
    raise ImportError(
        'pypicolcd requires pyusb (see "Install" in readme.md)'
    )

# TODO: remove about_msg and use pypicolcd.__doc__ (generated from
# docstring above) instead?

about_msg = """
pypicolcd  Copyright (C) 2018  Jake Gustafson
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions; open LICENSE file in text editor for details.
"""

# See
# <https://linuxconfig.org/
# tutorial-on-how-to-write-basic-udev-rules-in-linux>
# NOTE: double curly brace becomes literal (single):
dev_permission_msg = """
{user} must have root access or be given permission to manage
device id {device_id} (hex {device_hex}) via a udev rule file such as
/etc/udev/rules.d/50-picoUSB-{device_hex}.rules
  * containing:

SUBSYSTEM!="usb_device",
ACTION!="add", GOTO="datalogger_rules_end"
ATTR{{idVendor}}=="{vendor_hex}", ATTR{{idProduct}}=="{device_hex}", SYMLINK+="datalogger"
MODE="0666", OWNER="{user}", GROUP="root"
LABEL="datalogger_rules_end"

  * or for OLDER systems:

SUBSYSTEM !="usb_device",
ACTION !="add", GOTO="datalogger_rules_end"
SYSFS{{idVendor}}=="{vendor_hex}", SYSFS{{idProduct}}=="{device_hex}", SYMLINK+="datalogger"
MODE="0666", OWNER="{user}", GROUP="root"
LABEL="datalogger_rules_end"

  * debug via:\n"
    udevadm test /etc/udev/rules.d/50-picoUSB-{device_hex}.rules

* Then reload rules:
  udevadm control --reload-rules
  udevadm trigger
  # Then optionally:
  udevadm test /etc/udev/rules.d/50-picoUSB-{device_hex}.rules

* Then you must unplug the device!

* However, on some systems, the following may work:
  sudo usermod -a -G dialout {user}
  #- You must log out and log in after that.

"""

# The variable below an example provided for maintainers.
picoLCD_256x64_msg = dev_permission_msg.format(
    user="?",
    device_id="?",
    device_hex="c002",
    vendor_hex="04d8"
)


class DisconnectedError(Exception):
    pass


JSON_MAX = 8192


def view_traceback(indent=""):
    ex_type, ex, tb = sys.exc_info()
    print(indent + str(ex_type) + " " + str(ex) + ": ")
    traceback.print_tb(tb)
    del tb
    print("")


def to_bool(s):
    if s is True:  # MUST BE FIRST
        return True
    elif s is False:
        return False
    if (s is None) or (len(s) < 1):
        raise ValueError("to_bool got a blank value.")
    ret = None
    s_lower = s.lower()
    if s_lower == "false":
        ret = False
    elif s_lower == "0":
        ret = False
    elif s_lower == "no":
        ret = False
    elif s_lower == "off":
        ret = False
    else:
        ret = True
    return ret


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
height = 4  # can also be 2
ids = [0xc001, 0xc002]

DC_DICT = {}  # devices' characteristics dicts
tmp_dc = {}
tmp_dc["type"] = "text"
tmp_dc["name"] = "picoLCD 20x4"
tmp_dc["width"] = 20
tmp_dc["height"] = 4  # or 2, but that Product ID is unknown
tmp_dc["blockrows"] = 1
tmp_dc["zones"] = 1
tmp_dc["block_size"] = 80
# tmp_dc["chip_orientation"] = "landscape"
DC_DICT[str(0xc001)] = tmp_dc
tmp_dc = {}
tmp_dc["type"] = "graphics"
tmp_dc["name"] = "picoLCD 256x64"
# tmp_dc["chip_orientation"] = "portrait"
tmp_dc["ppb"] = 8  # VERTICAL pixels per byte
tmp_dc["width"] = 256
tmp_dc["height"] = 64
tmp_dc["blockrows"] = 8
tmp_dc["zones"] = 8
tmp_dc["block_size"] = 32  # ok since 8x8x32 == 256*(64/8) == 2048
tmp_dc["inverted"] = 1  # 1 as per official driver
#                         /picoLCDGraphic/Configs/lcd4linux.conf
tmp_dc["chip_size"] = 64 * (64 / tmp_dc["ppb"])  # 64x64 pixels,
#                                                  but 1-bit
tmp_dc["chip_count"] = 4
DC_DICT[str(0xc002)] = tmp_dc
tmp_dc = None


def get_pixel_color(canvas, x, y):
    """
    Try to get the pixel color from a Tkinter canvas.

    This function is useless, since it doesn't work for anything but
    rects, which we already know are there (This just gets a black
    rectangle for text)
    """
    ids = canvas.find_overlapping(x, y, x, y)
    if len(ids) > 0:
        index = ids[-1]  # -1 gets top (last) graphics instruction
        color = canvas.itemcget(index, "fill")
        color = color.upper()
        if color != '':
            return color.upper()
    else:
        print("[ pypicolcd ] WARNING in get_pixel_color: no color"
              " at " + str((x, y)))
    return "WHITE"


my_path = os.path.abspath(os.path.dirname(__file__))


def find_resource(path):
    ret = None
    in_module_path = os.path.join(my_path, path)
    if os.path.isfile(in_module_path):
        ret = in_module_path
        # print("FOUND: '{}'".format(ret))
    elif os.path.isfile(os.path.abspath(path)):
        ret = os.path.abspath(path)
        # print("FOUND: '{}'".format(ret))
    else:
        print("ERROR: resource is not present here or in"
              " '{}': '{}'".format(my_path, path))
    return ret


font_meta = {}
font_meta["ninepin"] = {}
font_meta["ninepin"]["filename"] = "ninepin.ttf"
font_meta["ninepin"]["default_size"] = 8
font_meta["zephyrean"] = {}
font_meta["zephyrean"]["filename"] = "zephyrea.ttf"
font_meta["zephyrean"]["default_size"] = 8
font_meta["zephyrean"]["note"] = "smallest 8pt readable font"
font_meta["flottflott"] = {}
font_meta["flottflott"]["filename"] = "Flottflott.ttf"
font_meta["flottflott"]["default_size"] = 11
font_meta["flottflott"]["note"] = "unreadable below font size 11"
font_meta["press start"] = {}
font_meta["press start"]["filename"] = "prstartk.ttf"
font_meta["press start"]["default_size"] = 6
font_meta["press start"]["note"] = "a pixel art font readable at 6pt"

for name, meta in font_meta.items():
    font_meta[name]["path"] = find_resource(
        os.path.join("fonts", meta["filename"])
    )
    if font_meta[name]["path"] is None:
        print("ERROR: missing '{}' (not in '{}')".format(
            meta["filename"],
            my_path
        ))


def get_font_meta(name):
    return font_meta.get(name.lower())


class PicoLCD:

    def __init__(self, verbose_enable=False):
        self.enable_permission_msg = True  # Only show this once.
        self._backlight_level = 0xFF
        self.framebuffer = None
        self.framebuffers = None
        self.change_enables = None
        self.verbose_enable = verbose_enable
        self.default_font = "ninepin"
        df = self.default_font
        self.enable_no_device_error = True
        self.default_font_size = font_meta[df]["default_size"]
        self._pos = (0, 0)
        self._f_cache = {}  # font cache
        self._s_cache = {}  # each character as stripes (pixel columns)
        self._im = None  # font rendering buffer
        # self.default_font_path = "fonts/ninepin.ttf"
        self.invalidate_dt = datetime.now()
        self.connect()
        self.preview_flag = False
        self._fps_interval = .4
        self._average_fps = None
        self._fps_last_frame_tick = None
        self._actual_frame_interval = None
        self._last_update_s = None
        self._fps_accumulated_time = 0.
        self._fps_accumulated_count = 0

    @staticmethod
    def get_font_names():
        return font_meta.keys()

    def connect(self, silent=False, enable_reset=True):
        self.dc = None  # device characteristics
        self.handle = None
        buses = usb.busses()
        this_idVendor = None
        this_idProduct = None
        self.error = None
        this_device = None
        found_count = 0
        self.blab("* Searching USB buses...")
        for bus in buses:
            for device in bus.devices:
                if device.idVendor == 0x04d8 and \
                        str(device.idProduct) in DC_DICT.keys():
                    #    device.idProduct in ids:
                    this_device = device
                    self.dc = DC_DICT[str(device.idProduct)]
                    this_idVendor = device.idVendor
                    this_idProduct = device.idProduct
                    self.blab("  * found " + self.dc["name"])
                    found_count += 1
        if self.ready():
            self.change_enables = []
            for block_i in range(self.dc["blockrows"]):
                for zone_i in range(self.dc["zones"]):
                    self.change_enables.append(0)
            if self.dc["type"] == "graphics":
                # block_count = self.dc["blockrows"] * self.dc["zones"]
                # self.framebuffers = []
                # for fb_i in range(block_count):
                #     self.framebuffer = [0] * (self.dc["block_size"])
                #     self.framebuffer[1] = 255
                #     if self.framebuffer[0] == 255:
                #         # deal with list initialization paranoia
                #         print("[ pycolcd ] ERROR: failed to create"
                #               " unique framebuffer elements")
                #         sys.exit(1)
                #     else:
                #         self.framebuffer[1] = 0
                #         self.framebuffers.append(self.framebuffer)
                pass
            else:
                # self.framebuffers = []
                # self.framebuffer = [0] * (self.dc["block_size"])
                # self.framebuffers.append(self.framebuffer)
                pass
            if enable_reset:
                self.reset_framebuffer(enable_reconnect=False)

        if this_device is not None:
            self.handle = this_device.open()
            try:
                self.handle.detachKernelDriver(0)
            except usb.USBError:
                # print("[ PicoLCD ] nothing to detach")
                pass
            try:
                self.handle.claimInterface(0)
                self.handle.setAltInterface(0)
                # print("[ pypicolcd ] claimed interface 0")
            except usb.core.USBError:
                self.dc = None
                # 50 is a priority level where lower numbers are first
                # (small x for lowercase--which is udev rule format):
                idv_s = '{:04x}'.format(this_idVendor)  # 4 hex digits
                idp_s = '{:04x}'.format(this_idProduct)  # 4 hex digits
                idp_i_s = str(this_idProduct)
                un = "yourusername"
                try:
                    import getpass
                    un = getpass.getuser()
                except Exception:
                    pass

                self.error = "  Claiming the interface failed. "
                if un == "root":
                    self.error += ("\n  You are root, so this shouldn't"
                                   " happen.")
                elif self.enable_permission_msg:
                    self.error = dev_permission_msg.format(
                        user=un,
                        device_id=idp_i_s,
                        device_hex=idp_s,
                        vendor_hex=idv_s
                    )
                    self.enable_permission_msg = False
                self.error += ("\n\n")
                self.error += ("* Connecting to a root hub or USB 2 or"
                               "\n  earlier port may solve the issue if"
                               "\n  " + un + " already has the correct"
                               " permissions to the device.")

                # print("[ PicoLCD ] ERROR--" + self.error + ": ")
                # NOTE: self.error is shown further down.
                # view_traceback()
        else:
            if self.error is None:
                self.error = ("ERROR: pypicolcd did not find a"
                              " known product ID connected to USB.")
        if self.error is not None:
            if (not silent) and self.enable_no_device_error:
                self.blab(
                    print("* pypicolcd found {} known"
                          " device(s)".format(found_count))
                )
                print(self.error)
                self.enable_no_device_error = False
        if self.ready():
            self.enable_no_device_error = True
            if enable_reset:
                self.clear()
            self.set_backlight(self._backlight_level,
                               enable_reconnect=False)
        return self.ready()

    def blab(self, msg, where=None):
        if self.verbose_enable:
            w_msg = ""
            if where is not None:
                w_msg = " in " + where
            else:
                curframe = inspect.currentframe()
                calframe = inspect.getouterframes(curframe, 2)
                w_msg = " in " + calframe[1][3]
            print("[ pypicolcd ] (verbose message {}) {}".format(w_msg, msg))

    def get_width(self):
        return self.dc["width"]

    def get_height(self):
        return self.dc["height"]

    def generate_fps(self):
        result = None
        # if self._last_update_s is not None:
        #     got_frame_delay = best_timer() - self._last_update_s
        self._last_update_s = best_timer()
        if self._fps_last_frame_tick is not None:
            # NOTE: best_timer() is in seconds
            self._actual_frame_interval = \
                best_timer() - self._fps_last_frame_tick
            self._fps_accumulated_time += self._actual_frame_interval
            self._fps_accumulated_count += 1
            if self._fps_accumulated_time >= self._fps_interval:
                self._average_fps = (
                    1.0
                    / (self._fps_accumulated_time
                       / float(self._fps_accumulated_count))
                )
                self._fps_accumulated_time = 0.0
                self._fps_accumulated_count = 0
                result = self._average_fps
            # if self._actual_frame_interval > 0.0:
            #     actual_fps = 1.0 / self._actual_frame_interval
        self._fps_last_frame_tick = best_timer()
        return result

    def set_fps_interval(self, seconds):
        self._fps_interval = seconds

    def get_fps(self):
        return self._average_fps

    def draw_rect(self, rect, on, filled=True):
        """
        Draw an exclusive rectangle to the (framebuffer and) LCD.

        Keyword arguments:
        rect -- tuple of tuples in format ((min_x, min_y),
            (max_x+1,max_y+1))
        on -- whether to turn the lcd pixel on (on is dark, since
            off lets backlight show through)
        """
        start_x, start_y = rect[0]
        end_x, end_y = rect[1]
        if filled:
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    self.set_pixel((x, y), on,
                                   refresh_enable=False)
        else:
            for y in range(start_y, end_y):
                tb = False
                if (y == start_y) or (y == end_y - 1):
                    tb = True
                for x in range(start_x, end_x):
                    lr = False
                    if (x == start_x) or (x == end_x - 1):
                        lr = True
                    if tb or lr:
                        self.set_pixel((x, y), on,
                                       refresh_enable=False)
        self.refresh()

    def wr(self, m, enable_reconnect=True):
        """
        Write bytes directly to the LCD (requires an opcode byte and the
        number of bytes that the opcode expects).

        Returns:
            bytes written
        """
        try:
            return self.handle.interruptWrite(
                usb.ENDPOINT_OUT+1,
                m,
                1000
            )
        except usb.core.USBError:
            if enable_reconnect:
                if self.reconnect():
                    return self.handle.interruptWrite(
                        usb.ENDPOINT_OUT + 1,
                        m,
                        1000
                    )
                else:
                    raise DisconnectedError("Reconnecting to the device"
                                            " failed.")
        except AttributeError:
            # 'NoneType' object has no attribute 'interruptWrite'
            if enable_reconnect:
                if self.reconnect():
                    return self.handle.interruptWrite(
                        usb.ENDPOINT_OUT + 1,
                        m,
                        1000
                    )
                else:
                    raise DisconnectedError("Reconnecting to the device"
                                            " failed.")
        return 0

    def reconnect(self, silent=False):
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        self.blab("* " + calframe[1][3] + " is reconnecting...")
        result = self.connect(silent=silent, enable_reset=False)
        if result:
            # self.reset_framebuffer(enable_reconnect=False)
            self.invalidate()
            self.refresh(enable_reconnect=False)
        return result

    def transfer_row(self, dst_br_i, src_br_i):
        """
        Transfer row src_br_i to dst_br_i then erase row src_br_i
        (for graphics type models only!).

        * does NOT refresh, but does invalidate so later refresh will
        work
        """
        for zone_i in range(self.dc["zones"]):
            src_fb_i = src_br_i * self.dc["zones"] + zone_i
            dst_fb_i = dst_br_i * self.dc["zones"] + zone_i
            self.framebuffers[dst_fb_i] = self.framebuffers[src_fb_i]
            self.framebuffers[src_fb_i] = [0] * (self.dc["block_size"])
            self.change_enables[src_fb_i] = -1
            self.change_enables[dst_fb_i] = -1

    def reset_row(self, blockrow_i):
        """
        Reset one row of block buffers.
        (for graphics type models only!).

        * does NOT refresh, but does invalidate so later refresh will
        work
        """
        for zone_i in range(self.dc["zones"]):
            fb_i = blockrow_i * self.dc["zones"] + zone_i
            self.framebuffers[fb_i] = [0] * (self.dc["block_size"])
            self.change_enables[fb_i] = -1

    def reset_framebuffer(self, enable_reconnect=True):
        self.change_enables = []
        self.framebuffers = []
        # for block_i in range(self.dc["blockrows"]):
        #     for zone_i in range(self.dc["zones"]):
        #         self.change_enables.append(False)
        if not self.ready():
            if enable_reconnect:
                self.reconnect()
        if not self.ready():
            raise DisconnectedError("reconnect failed"
                                    " in reset_framebuffer")
        block_count = self.dc["blockrows"] * self.dc["zones"]
        for fb_i in range(block_count):
            self.change_enables.append(0)
            self.framebuffer = [0] * (self.dc["block_size"])
            self.framebuffer[1] = 255
            if self.framebuffer[0] == 255:
                # deal with list initialization paranoia
                raise RuntimeError("[ pycolcd ] ERROR: failed to create"
                                   " unique framebuffer elements")
            else:
                self.framebuffer[1] = 0
                self.framebuffers.append(self.framebuffer)

    def smaller_rect(self, outline, offset=1):
        return ((outline[0][0]+offset, outline[0][1]+offset),
                (outline[1][0]-offset, outline[1][1]-offset))

    def larger_rect(self, outline, offset=1):
        return ((outline[0][0]-offset, outline[0][1]-offset),
                (outline[1][0]+offset, outline[1][1]+offset))

    def _cache_font(self, font_path, font_size, threshold):
        is_ok = True

        if font_size is None:
            font_size = self.default_font_size
        default_font_path = font_meta[self.default_font]["path"]
        if font_path is None:
            font_path = default_font_path
            self.blab("reverted to default font '"
                      + font_path + "'")
            if not os.path.isfile(font_path):
                print("[ PicoLCD ] ERROR in draw_text:"
                      + " missing default font '"
                      + font_path + "'")
                is_ok = False
        elif not os.path.isfile(font_path):
            try_path = os.path.join("fonts", font_path)
            if os.path.isfile(try_path):
                font_path = try_path
            else:
                print("[ PicoLCD ] ERROR in draw_text:"
                      " font '" + font_path + "' not found.")
                is_ok = False
        if not is_ok:
            return None, None, None

        if threshold is None:
            threshold = .5
            for_msg = ""
            # if font_path is None and font_size > 8:
            if font_path == default_font_path:
                if font_size > 8:
                    threshold = .02
                else:
                    threshold = .03
                for_msg = (" (adjusted from .5 to {} to accommodate"
                           " edges of blocks in ninepin"
                           " font)".format(threshold))
            self.blab("threshold was None so reverted to default"
                      + for_msg + ": "
                      + str(threshold))

        fss = str(font_size)
        if font_path not in self._f_cache:
            self._f_cache[font_path] = {}
        if fss not in self._f_cache[font_path]:
            self._f_cache[font_path][fss] = \
                ImageFont.truetype(font_path, font_size)

        return font_path, font_size, threshold

    def push_text(self, text, erase_behind_enable=False,
                  refresh_enable=True, spacing_x=1, scroll_count=1):
        """
        This is an optimized vertical scrolling text function (It only
        scrolls when necessary and it uses an 8-pixel-high font that
        fits into one buffer and fits into the stripe cache).
        """

        results = None, None
        abs_x, abs_y = self._pos
        if not self.ready():
            raise DisconnectedError("The device is not connected.")
        dst_w = self.dc["width"]
        dst_h = self.dc["height"]
        if self._im is None:
            self._im = Image.new('RGBA', (dst_w, dst_h),
                                 (255, 255, 255, 0))
        # if x < 0 or y < 0 or x > dst_w or y > dst_h:
            # return False
        zone_width = dst_w / self.dc["zones"]
        font_path = font_meta[self.default_font]["path"]
        font_size = self.default_font_size
        threshold = .5
        if self.dc["type"] != "graphics":
            print("[ PicoLCD ] ERROR in push_text: this function"
                  " is not implemented except for graphics type"
                  " displays.")
            return None, None
        fss = str(font_size)
        sc = self._s_cache
        fc = self._f_cache
        if font_path not in self._f_cache:
            self._f_cache[font_path] = {}
        if fss not in self._f_cache[font_path]:
            self._f_cache[font_path][fss] = \
                ImageFont.truetype(font_path, font_size)
        # font_path, font_size, threshold = \
            # self._cache_font(font_path, font_size, threshold)
        this_sc = None  # the stripe cache for the current
        # [font][size][character]
        if font_path not in sc:
            sc[font_path] = {}
        if fss not in sc[font_path]:
            sc[font_path][fss] = {}
        is_escaped = False
        _d = ImageDraw.Draw(self._im)
        for c in text:
            generate_enable = False
            this_sc = None
            this_spacing_x = spacing_x

            if c not in sc[font_path][fss]:
                try:
                    sc[font_path][fss][c] = []
                except TypeError as e:
                    print("font_path:'{}'; fss:'{}'; c:'{}'".format(
                        font_path,
                        fss,
                        c
                    ))
                    raise e
                this_sc = sc[font_path][fss][c]
                generate_enable = True
                # print("generate_enable: {}; len(this_sc):"
                #       " {}".format(generate_enable, len(this_sc)))
            if generate_enable:

                try:
                    fnt = fc[font_path][fss]
                    if len(c.strip()) > 0:
                        self.blab("* drawing glyph '{}'...".format(c))
                        _d.text((0, 0), c, font=fnt,
                                fill=(255, 255, 255, 255))
                        start_enable = False
                        x = 0
                        im = self._im
                        # print("* generating '{}'...".format(c))
                        while x < 256:  # or until end of character
                            stripe_enable = False
                            stripe = 0x00  # 1-byte vertical stripe: 8px
                            for y in range(8):
                                r, g, b, a = im.getpixel((x, y))
                                # print("  {} {}".format(
                                #     x,
                                #     im.getpixel((x, y))
                                # ))
                                alpha = float(a) / 255.
                                if alpha > threshold:
                                    stripe_enable = True
                                    stripe |= (1 << y)
                            if stripe_enable:
                                start_enable = True
                                this_sc.append(stripe)
                            else:
                                if start_enable:
                                    # found end of letter
                                    break
                            x += 1
                        self.blab("* erasing rect")
                        _d.rectangle((0, 0, x+1, 8),
                                     fill=(255, 255, 255, 0))
                        # self._im.putalpha(0)
                    else:
                        self.blab("* handling space")
                        # " " (space)
                        space_w = int(font_size*.4)
                        # less than width of ~6px wide letters

                        # NOTE: append since this_sc is a reference!
                        # this_sc.append([0]*space_w)

                        sc[font_path][fss][c] = [0]*space_w
                        # sc[font_path][fss][c] = this_sc
                        this_sc = sc[font_path][fss][c]
                        # x += space_w
                except Exception as e:
                    raise e
                finally:
                    if _d is not None:
                        self.blab("* deleting _d")
                        del _d
                        _d = None
                # print("* '{}' became {} wide...".format(c,
                #                                         len(this_sc)))
            else:
                self.blab("* loading existing stripe cache")
                this_sc = sc[font_path][fss][c]

            if (c == "\\") and (not is_escaped):
                is_escaped = True
                continue
            if _d is not None:
                del _d
                _d = None
            tab_w = 32
            if c == "\n":
                is_escaped = True
                c = "n"
            elif c == "\r":
                is_escaped = True
                c = "r"
            elif c == "\t":
                is_escaped = True
                c = "t"

            if is_escaped:
                is_escaped = False
                if c == "n":
                    abs_x = 0
                    abs_y += 8
                    continue
                elif c == "r":
                    abs_x = 0
                    continue
                elif c == "t":
                    abs_x += tab_w
                    tab_slot_i = abs_x // tab_w
                    abs_x = tab_slot_i * tab_w
                    continue
                # otherwise count it as a literal
            self.blab("* writing stripes")
            if abs_x + len(this_sc) > dst_w:
                abs_x = 0
                abs_y += 8
            if abs_y + 8 > dst_h:  # == is ok since is exclusive rect
                # then scroll
                if scroll_count > len(this_sc):
                    # NOTE: the length of stripe cache is the width
                    # of the character, since each byte is one 1x8
                    # 1-bit stripe.
                    self.clear()
                else:
                    br_count = self.dc["blockrows"]
                    for dst_br_i in range(br_count):
                        src_br_i = dst_br_i + scroll_count
                        if src_br_i >= br_count:
                            # if nothing to scroll, erase destination
                            self.reset_row(dst_br_i)
                        else:
                            self.transfer_row(dst_br_i, src_br_i)
                abs_y -= scroll_count * 8  # Size of byte is the
                #                            mandatory font height for
                #                            this method.
                if abs_y < 0:
                    abs_y = 0

            x = None
            zones = []
            block_i = int(abs_y/self.dc["blockrows"])

            count_x = 0
            for s_i in range(len(this_sc)):
                x = s_i + abs_x
                zone_i = int(x/zone_width)
                if zone_i not in zones:
                    zones.append(zone_i)
                fb_i = block_i * self.dc["zones"] + zone_i
                fb = self.framebuffers[fb_i]
                byte_i = x % self.dc["block_size"]
                if byte_i >= 0 and byte_i < len(fb):
                    fb[byte_i] = this_sc[s_i]
                else:
                    break
                count_x += 1
            self.invalidate(zones=zones, blocks=[block_i])
            abs_x += count_x + spacing_x
            # scrolling is caught next time, see start of method above
        self._pos = abs_x, abs_y
        if self.ready() and refresh_enable:
            return self.refresh()
        return False

    def draw_text(self, row, col, text, font=None, font_path=None,
                  font_size=None, threshold=None,
                  erase_behind_enable=False, refresh_enable=True,
                  erase_rect=None):
        """
        Draw text at the row and column specified, using 6x8 slots:
        5x7 text (maximum, not monospaced) plus 1px spacing.

        For information on other parameters, see the draw_text_at
        documentation.
        """
        results = None, None
        pos = col, row  # col,row format is y,x order
        if self.dc["type"] == "graphics":
            pos = (col * 6, row * 8)
        return self.draw_text_at(
            pos, text, font=font,
            font_size=font_size,
            threshold=threshold,
            erase_behind_enable=erase_behind_enable,
            refresh_enable=refresh_enable,
            erase_rect=erase_rect)

    def draw_text_at(self, pos, text, font=None, font_size=None,
                     font_path=None, threshold=None,
                     erase_behind_enable=False, refresh_enable=True,
                     erase_rect=None):
        """
        Draw text to the (framebuffer and) LCD.

        Keyword arguments:
        row,col -- the y,x location (in that order; though if
            picolcd.dc["type"] is graphics, it will be a pixel location
            where row is the middle of the letters)
        font -- If you provide the name of a prepackaged font (case
            insensitive), then you do not have to specify font_path.
            This option only works if picolcd.dc["type"] is "graphics".
        font_path -- Specify a ttf file. This option only works for
            devices where picolcd.dc["type"] is "graphics".
        font_size -- Specify a font size in points. This option is only
            available for devices where picolcd.dc["type"] is
            "graphics".
        threshold -- must be this opaque or higher--fine tuning may
            improve readability for certain fonts at small sizes
            (higher values make font slightly thinner). If None, .5
            will be used (.02 if default font with font size > 8, to
            catch edges of squares)
        refresh_enable -- whether to write the invalidated area from the
            framebuffers to the device (however, for text type devices,
            this is ignored and data is always written)
        erase_behind_enable -- erase behind (calculates rect unless
            erase_rect is not None
        erase_rect -- erase this rect first (turns on
            erase_behind_enable automatically)

        Returns:
            Only if graphics type device, and only if
            erase_behind_enable, the method returns rect actually drawn
            in ((min_x, min_y), (max_x+1,max_y+1)) format (this can be
            saved for your future use, such as if you do
            refresh_enable=False just to get font metrics, then clear,
            then draw what you really wanted, or just record the
            numbers for future use so you don't have to repeat those
            calls for each run--it is also not repeated inside of this
            function if you pass an erase_rect)
        """
        results = None, None
        if (font_path is None) and (font is not None):
            meta = get_font_meta(font)
            if meta is None:
                raise ValueError("The font is not known. Try (case"
                                 " doesn't matter):"
                                 " {}".format(font_meta.keys()))
            font_path = meta["path"]
            if font_size is None:
                default_size = meta.get("default_size")
                if default_size is not None:
                    font_size = default_size

        if erase_rect is not None:
            erase_behind_enable = True
        if self.dc["type"] == "graphics":
            # pos = (col, row)  # column is x, row is y
            on_count = 0
            is_ok = True
            font_path, font_size, threshold = \
                self._cache_font(font_path, font_size, threshold)
            if font_path is None:
                return None, None
            size = self.dc["width"], self.dc["height"]
            # intentionally start with useless values:
            minimums = [size[0], size[1]]
            maximums = [0, 0]
            if erase_rect is not None:
                self.blab("* drawing erase_rect")
                self.draw_rect(erase_rect, False)
            if self._im is None:
                self.blab("* creating _im font buffer")
                self._im = Image.new('RGBA', size, (255, 255, 255, 0))
            fnt = self._f_cache[font_path][str(font_size)]
            # self.blab("* getting draw buffer from _im")
            _d = ImageDraw.Draw(self._im)
            try:
                self.blab("* drawing text '{}' at {} using fnt {} on PIL"
                          " Draw object".format(text, pos, fnt))
                # TODO: _d.text sometimes causes
                # `Segmentation fault (core dumped)`
                # or
                # ```
                # corrupted size vs. prev_size
                # Aborted (core dumped)
                # ```:
                # or
                # ```
                # munmap_chunk(): invalid pointer
                # lcd-fb.service: Main process exited, code=dumped, status=6/ABRT
                # lcd-fb.service: Failed with result 'core-dump'.
                # ```
                _d.text(pos, text, font=fnt, fill=(255, 255, 255, 255))
                pos_list = []
                self.blab("* drawing text from buffer")
                for src_y in range(size[1]):
                    if erase_rect is None:
                        for src_x in range(size[0]):
                            dest_x, dest_y = src_x, src_y
                            r, g, b, a = self._im.getpixel(
                                (src_x, src_y)
                            )
                            alpha = float(a) / 255.
                            if alpha >= threshold:
                                on_count += 1  # for debugging only
                                if erase_behind_enable:
                                    if dest_x > maximums[0]:
                                        maximums[0] = dest_x
                                    if dest_x < minimums[0]:
                                        minimums[0] = dest_x
                                    if dest_y > maximums[1]:
                                        maximums[1] = dest_y
                                    if dest_y < minimums[1]:
                                        minimums[1] = dest_y
                                    pos_list.append((dest_x, dest_y))
                                else:
                                    self.set_pixel((dest_x, dest_y),
                                                   True,
                                                   refresh_enable=False)
                    else:
                        # separate x loop for optimization
                        for src_x in range(size[0]):
                            dest_x, dest_y = src_x, src_y
                            r, g, b, a = self._im.getpixel(
                                (src_x, src_y)
                            )
                            alpha = float(a) / 255.
                            if alpha >= threshold:
                                on_count += 1  # for debugging only
                                self.set_pixel((dest_x, dest_y), True,
                                               refresh_enable=False)
                if erase_behind_enable and (erase_rect is None):
                    # generate and draw the erase rect using the
                    # minimums & maximums, then draw the postponed text
                    # pixels (from pos_list):
                    results = (tuple(minimums),
                               (maximums[0]+1, maximums[1]+1))
                    # self.blab("* generate and draw the erase rect")
                    self.draw_rect(results, False)
                    # self.blab("* draw post_list")
                    for this_pos in pos_list:
                        self.set_pixel(this_pos, True,
                                       refresh_enable=False)
                    _d.rectangle(results, fill=(255, 255, 255, 0))
                else:
                    # self.blab("* wipe _d buffer")
                    # rect can be ((x,y),(x2,y2)) or (x,y,x2,y2):
                    rect = (0, 0, self.dc["width"], self.dc["height"])
                    _d.rectangle(rect, fill=(255, 255, 255, 0))
            except Exception as e:
                raise e
            finally:
                if _d is not None:
                    self.blab("* deleting _d finally")
                    del _d
                    _d = None
            # for y in range(self.dc["height"]):
                # for x in range(start_x, self.dc["width"]):
            if on_count < 1:
                print("[ PicoLCD ] WARNING in draw_text: offscreen"
                      + " buffer had " + str(on_count)
                      + " text pixels")
            if refresh_enable:
                self.refresh()
        else:
            col, row = pos  # col, row format is in y,x order
            addr = {0: 0x80, 1: 0xc0, 2: 0x94, 3: 0xd4}[row] + col
            self.blab("* send 0x94 command (non-graphics text)")
            result = self.wr(bytes(0x94, 0x00, 0x01, 0x00, 0x64, addr))
            if result < 1:
                print("[ pypicolcd ] ERROR: " + str(result)
                      + "byte(s) written for address")
            self.blab("* send OUT_REPORT_DATA command")
            self.wr(bytes(OUT_REPORT_DATA, 0x01, 0x00, 0x01, len(text))
                    + text)

    # draw image to lcd (bigger than screen or negative pos is ok)
    # pos: (x,y) coords for where to place left top corner of image
    # threshold: lightness (r+g+b/765) must be threshold or higher,
    #   to be white (not set) otherwise is black (on)
    #   if left at default, dithering will be used instead
    # brightness: multiplier for dithering, so only applies if
    #   threshold=None
    def draw_image(self, pos, path, threshold=None, invert_enable=False,
                   brightness=1.0):
        brightness *= 2
        try:
            im = Image.open(path)
            rgb_im = im.convert('RGB')
            width, height = im.size
            dst_w = self.dc["width"]
            dst_h = self.dc["height"]
            src_y = 0
            errors = []

            while src_y < height:
                dst_y = src_y + pos[1]
                if dst_y >= 0:
                    if dst_y < dst_h:
                        src_x = 0
                        while src_x < width:
                            dst_x = src_x + pos[0]
                            if dst_x >= 0:
                                if dst_x < dst_w:
                                    r, g, b = rgb_im.getpixel(
                                        (src_x, src_y))
                                    if threshold is not None:
                                        val = float(r + g + b) / 765.
                                        # on = val >= threshold
                                        if val >= threshold:
                                            self.set_pixel(
                                                (dst_x, dst_y),
                                                invert_enable,
                                                refresh_enable=False)
                                        else:
                                            self.set_pixel(
                                                (dst_x, dst_y),
                                                not invert_enable,
                                                refresh_enable=False)
                                    else:
                                        total = r + g + b
                                        # threshold_i = 382  # 765 / 2
                                        ri = random.randrange(765)
                                        # on is dark (blocks backlight)
                                        # if not desired,
                                        # use invert_enable
                                        # on = ri <= threshold_i
                                        on = total * brightness < ri
                                        if invert_enable:
                                            on = not on
                                        self.set_pixel(
                                            (dst_x, dst_y),
                                            on,
                                            refresh_enable=False)
                                    src_x += 1
                                else:
                                    break
                            else:
                                src_x += -dst_x
                        src_y += 1
                    else:
                        break
                else:
                    src_y += -dst_y
            self.refresh()
        except Exception as e:
            print("[ PicoLCD ] ERROR--could not finish loading image:"
                  " {}".format(e))
            # view_traceback()

    # Invalidate rectangle of lcd to force refresh to refresh them
    #   next time refresh is called (if no params, then entire screen:
    #   zones 0 to picolcd.dc["zones"]
    #   and blocks 0 to picolcd.dc["blockrows"])
    # If you want a non-rectangle, set framebuffer numbers in
    #   picolcd.change_enables manually instead.
    # zones: list of zone indices where each index is 0 to
    #   picolcd.dc["zones"]
    # zone_stop_x: refresh part of last zone in zone list (if -1,
    #   refresh entire zone; if 0, do not refresh anything so calling
    #   this method was a waste of time)
    def invalidate(self, zones=None, blocks=None, zone_stop_x=-1,
                   enable_reconnect=True):
        if not self.ready():
            if enable_reconnect:
                if not self.reconnect():
                    return False
            else:
                return False
        self.invalidate_dt = datetime.now()
        self.blab("* invalidate")
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
        last_zone_i = None
        try:
            even_z_i_i = -1
            for zone_i_i in reversed(range(len(zones))):
                zone_i = zones[zone_i_i]
                if (zone_i % 2 == 1):
                    try:
                        even_z_i_i = zones.index(zone_i - 1)
                    except ValueError:
                        even_z_i_i = -1
                    if (even_z_i_i > -1):
                        del zones[even_z_i_i]
        except Exception as e:
            print("[ PicoLCD ] ERROR--Could not finish invalidate {"
                  + " last_zone_i: " + str(last_zone_i)
                  + "; zones: " + str(zones)
                  + "}: {}".format(e))
        zsx = -1
        for block_i in blocks:
            zl = len(zones)
            for zii in range(zl):
                zone_i = zones[zii]
                fb_i = block_i * self.dc["zones"] + zone_i
                self.change_enables[fb_i] = zsx
                if zii == zl - 1:
                    zsx = zone_stop_x
                # self.refresh_block(zone_i, block_i)

    def refresh(self, enable_reconnect=True):
        """
        Refresh all or part of lcd from framebuffers where invalidated
        (where set_pixel was called or other operation was done). For
        advanced use, such as if you drew to a framebuffer manually,
        call invalidate first to inform PicoLCD which framebuffers
        changed.
        """
        if not self.ready():
            if enable_reconnect:
                self.reconnect()
        if not self.ready():
            return False
        self.blab("* refresh")
        for fb_i in range(len(self.change_enables)):
            if self.change_enables[fb_i] != 0:
                block_i = int(fb_i / self.dc["blockrows"])
                zone_i = fb_i % self.dc["blockrows"]
                self.refresh_block(
                    zone_i, block_i,
                    zone_stop_x=self.change_enables[fb_i],
                    enable_reconnect=enable_reconnect
                )
        return True

    def refresh_block(self, zone_i, block_i, zone_stop_x=-1,
                      enable_reconnect=True):
        """
        Refresh all or part of an lcd block from the matching
        framebuffer.

        Keyword arguments:
        zone_stop_x -- refresh part of zone (if -1,
          refresh entire zone; if 0, do not refresh anything so calling
          this method was a waste of time); this method changes fps of
          drawing one character at a time from 7.6 to 8.1 (though goes
          back down over time probably since characters overlap block
          edges)
        """
        self.blab("* refresh zone {} block {}".format(zone_i, block_i))
        # self._cmd3_len_i = 11
        # self._cmd4_len_i = 4
        result = 0
        data_len = 32  # always 32 so you don't lose your place
        #                (positioning is relative when accessing
        #                an odd zone aka right side of a chip)
        if zone_stop_x == 0:
            return 0
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
            fb = self.framebuffers[
                block_i * self.dc["zones"] + (zone_i-1)
            ]
            cmd3.extend(fb)
            self.blab("* write even zone")
            result += self.wr(cmd3, enable_reconnect=enable_reconnect)
            cmd4 = [
                OUT_REPORT_DATA,
                chipsel | 0x01,
                0x00,
                0x00,
                data_len
            ]
            fb = self.framebuffers[block_i * self.dc["zones"] + zone_i]
            if zone_stop_x > -1:
                cmd4[len(cmd4) - 1] = zone_stop_x
                cmd4.extend(fb[:zone_stop_x])
            else:
                cmd4.extend(fb)
            self.blab("* write odd zone")
            result += self.wr(cmd4, enable_reconnect=enable_reconnect)
        else:
            fb = self.framebuffers[block_i * self.dc["zones"] + zone_i]
            if zone_stop_x > -1:
                cmd3[len(cmd3) - 1] = zone_stop_x
                cmd3.extend(fb[:zone_stop_x])
            else:
                cmd3.extend(fb)
            self.blab("* write odd zone")
            result += self.wr(cmd3, enable_reconnect=enable_reconnect)

    def get_pixel(self, pos):
        """Get a one-bit pixel.

        Returns
            A boolean value indicating whether the pixel value is
            currently 1 according to the framebuffer.
        """
        x, y = pos
        dst_w = self.dc["width"]
        dst_h = self.dc["height"]
        # if x < 0 or y < 0 or x > dst_w or y > dst_h:
        #     return False
        zone_width = dst_w / self.dc["zones"]
        zone_i = int(x/zone_width)
        block_i = int(y/self.dc["blockrows"])
        fb_i = block_i * self.dc["zones"] + zone_i
        bit_i = y % self.dc["ppb"]
        byte_i = x % self.dc["block_size"]
        pixel = 1 << bit_i
        if (fb_i < 0) or (fb_i >= len(self.framebuffers)):
            raise RuntimeError("[ PicoLCD ] ERROR in get_pixel: buffer "
                               + str(fb_i) + " does not exist in "
                               + str(len(self.framebuffers)) + "-len"
                               + " buffer list.")

        framebuffer = self.framebuffers[fb_i]
        result = framebuffer[byte_i]
        return (result & pixel) > 0

    def set_pixel(self, pos, on, refresh_enable=True,
                  force_refresh_enable=False):
        """
        Set a one-bit pixel to the value of on (invalidate block if
        pixel differs from framebuffer or force_refresh_enable is True).

        Sequential arguments:
        on -- determines whether to turn the pixel on or off

        Keyword arguments:
        refresh_enable -- draw the affected block from framebuffers
            (if False, you will have to call refresh later (which will
            draw all invalidated blocks automatically)
        force_refresh_enable -- draw even if the pixel does not differ
            from framebuffer
        """
        # NOTE: one byte covers 8 pixels on y axis from landscape view
        x, y = pos
        if force_refresh_enable:
            refresh_enable = True
        if not self.ready():
            print("* set_pixel attempting to connect...")
            if not self.reconnect():
                raise DisconnectedError("The device is not connected.")
        dst_w = self.dc["width"]
        dst_h = self.dc["height"]
        # if x < 0 or y < 0 or x > dst_w or y > dst_h:
        #     return 0
        zone_width = dst_w / self.dc["zones"]
        zone_i = int(x/zone_width)
        block_i = int(y/self.dc["blockrows"])
        fb_i = block_i * self.dc["zones"] + zone_i
        bit_i = y % self.dc["ppb"]
        byte_i = x % self.dc["block_size"]
        pixel = 1 << bit_i
        # self.blab(str((x,y)) + " results in"
        #             + " framebuffer[" + str((fb_i)) + "]"
        #             + " zone,block=" + str((zone_i, block_i))
        #             + " byte=" + str(byte_i) + " bit=" + str(bit_i))
        if (fb_i < 0) or (fb_i >= len(self.framebuffers)):
            print("[ PicoLCD ] ERROR in set_pixel at " + str(pos)
                  + ": buffer " + str(fb_i) + " does not exist in "
                  + str(len(self.framebuffers)) + "-len buffer list.")
            return 0
        framebuffer = self.framebuffers[fb_i]
        result = framebuffer[byte_i]
        # TODO: account for "inverted" mode
        if on:
            if result | pixel != result:
                framebuffer[byte_i] |= pixel
                self.change_enables[fb_i] = byte_i + 1
            else:
                if not force_refresh_enable:
                    refresh_enable = False
                else:
                    self.change_enables[fb_i] = byte_i + 1
        else:
            if result & pixel > 0:
                framebuffer[byte_i] ^= pixel
                self.change_enables[fb_i] = byte_i + 1
            else:
                if not force_refresh_enable:
                    refresh_enable = False
                else:
                    self.change_enables[fb_i] = byte_i + 1
        if refresh_enable:
            # msg = "refreshing"
            # if self.change_enables[fb_i] == 0:
            #     msg = "not refreshing"
            # print(msg + " " + str((zone_i, block_i)))
            self.refresh_block(zone_i, block_i, zone_stop_x=byte_i+1)

    def set_preview_flag(self, dirty):
        self.preview_flag = dirty

    def ready(self):
        return self.dc is not None

    def set_byte(self, pos, dat_b, refresh_enable=True,
                 force_refresh_enable=False):
        """
        Set a byte (1x8 pixel vertical strip) on the LCD.

        Keyword arguments:
        dat_b -- one byte containing (8) 1-bit pixels VERTICALLY
        """
        # NOTE: one byte covers 8 pixels on y axis from landscape view
        if not self.ready():
            print("* set_byte is attempting to reconnect...")
            if not self.reconnect():
                raise DisconnectedError("The device is not connected.")
        x, y = pos
        if force_refresh_enable:
            refresh_enable = True
        dst_w = self.dc["width"]
        dst_h = self.dc["height"]
        # if x < 0 or y < 0 or x > dst_w or y > dst_h:
        #     return 0
        zone_width = dst_w / self.dc["zones"]
        zone_i = int(x/zone_width)
        block_i = int(y/self.dc["blockrows"])
        fb_i = block_i * self.dc["zones"] + zone_i
        bit_i = y % self.dc["ppb"]
        byte_i = x % self.dc["block_size"]
        pixel = dat_b
        # self.blab(" " + str((x,y)) + " results in"
        #           + " framebuffer[" + str((fb_i)) + "]"
        #           + " zone,block=" + str((zone_i, block_i))
        #           + " byte=" + str(byte_i) + " bit=" + str(bit_i))
        # if (fb_i < 0) or (fb_i >= len(self.framebuffers)):
        #     print("[ PicoLCD ] ERROR in set_pixel: buffer "
        #           + str(fb_i) + " does not exist in "
        #           + str(len(self.framebuffers)) + "-len buffer list.")
        #     return 0
        framebuffer = self.framebuffers[fb_i]
        result = framebuffer[byte_i]
        # TODO: account for "inverted" mode
        if pixel != result:
            framebuffer[byte_i] = pixel
            self.change_enables[fb_i] = byte_i + 1
        else:
            if not force_refresh_enable:
                refresh_enable = False
            else:
                self.change_enables[fb_i] = byte_i + 1
        if refresh_enable:
            # msg = "refreshing"
            # if self.change_enables[fb_i] == 0:
            #     msg = "not refreshing"
            # print(msg + " " + str((zone_i, block_i)))
            self.refresh_block(zone_i, block_i, zone_stop_x=byte_i+1)

    def clear(self, enable_reconnect=True):
        self.reset_framebuffer(enable_reconnect=enable_reconnect)
        if self.ready():
            self.invalidate(enable_reconnect=enable_reconnect)
            self.refresh(enable_reconnect=enable_reconnect)
            self.preview_flag = True

    def set_backlight_f(self, level, enable_reconnect=True):
        """
        Set the backlight level.

        Sequential arguments:
        level -- a float, 0.0-1.0, for the backlight, where 1.0 is 100%
        """
        try:
            self.set_backlight(self, int(round(level*255.0)),
                               enable_reconnect=enable_reconnect)
        except ValueError:
            raise ValueError("The level must be 0.0-1.0")

    def set_backlight(self, level, enable_reconnect=True):
        """
        Set the backlight level.

        Sequential arguments:
        level -- an integer, 0-255, for the backlight, where 255 is 100%
        """
        # NOTE: NOT 1-1000, default 800 as asserted by
        # mhswa Aug 27, 2018:
        # https://forum.netgate.com/topic/134151/lcd4linux-picolcd/8
        try:
            b = int(level)
        except TypeError:
            raise TypeError("The level must be an integer 0-255")
        if b != level:
            raise TypeError("The level must be an integer 0-255")
        if (b >= 0) and (b <= 255):
            self.wr([OUT_REPORT_LCD_BACKLIGHT, b],
                    enable_reconnect=enable_reconnect)
            self._backlight_level = b
        else:
            raise ValueError("The level must be 0-255")

    def leds(self, state):
        # TODO: test this, and do something with the return
        self.wr([OUT_REPORT_LED_STATE, state])

    def flash(self):
        prev_level = self._backlight_level
        # for level in (list(range(20, 0, -1)) + list(range(0, 21))):
        standard_step = 10
        step = standard_step
        flash_max = 255
        flash_min = 0
        if flash_min < prev_level:
            # This is always True unless flash_min is not 0
            step *= -1
        levels = list(range(prev_level, flash_min, step))
        levels += list(range(flash_min, flash_max, standard_step))
        step = standard_step
        if prev_level < flash_max:
            # This is always True unless flash_max is not 255
            step *= -1
        levels += list(range(flash_max, prev_level, step))

        for level in levels:
            self.set_backlight(level)
            time.sleep(.01)
        self.set_backlight(prev_level)


if __name__ == "__main__":
    from datetime import datetime
    p = None
    if p is None:
        p = PicoLCD()
    if p.dc is None:
        error = p.error
        if error is None:
            error = "ERROR: Could not load device for unknown reason."
            print(error)
        # else error was already printed by p
        exit(1)
    p.clear()
    p.draw_text(0, 0, "It worked!")
    y = 3
    pixel_y = round(p.dc["height"] / 2)
    if pixel_y > y:
        y = pixel_y
    p.draw_text(y, 0, datetime.now().ctime()[:20])
    print("You can use this module like:")
    print("  from pypicolcd import PicoLCD")
    print("  p = PicoLCD()")
