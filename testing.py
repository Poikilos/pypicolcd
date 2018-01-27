#!/bin/env python3
# (tests for) pypicolcd, a module for driverless writing to picoLCD
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

from datetime import datetime
import time
import binascii
try:
    from picolcd import PicoLcd
    try:
        from picolcd import OUT_REPORT_CMD_DATA
    except:
        print("Missing OUT_REPORT_CMD_DATA")
    try:
        from picolcd import OUT_REPORT_DATA
    except:
        print("Missing OUT_REPORT_DATA")
except ImportError:
    print("requires picolcd.py such as from")
    print("  http://excamera.com/sphinx/article-picolcd.html")
    print("which requires pyusb")
    print("such as via:")
    print("  sudo pip install pyusb")
    # only catch ImportError, so exceptions in picolcd will be shown
try:
    import Tkinter as tk
    import tkFont
    import ttk
except ImportError:  # Python 3
    import tkinter as tk
    import tkinter.font as tkFont
    import tkinter.ttk as ttk
p = None
cmd_len = None
data_len = 0x01
pixel = 0xFF

blank_cmd = [
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00
]
# clears top (landscape left) of each chip (each chip is 64x64 pixels)
cmd3 = [
    OUT_REPORT_CMD_DATA,
    0x00, # chipsel | chipside,  # this is a BYTE
    0x02,
    0x00,
    0x00,
    0xb8, # sidestep,  # 0xb8|sidestep,  # 0xb8|line,
    0x00,
    0x00,
    0x40, # 0x40, if this is 00, each identical command will be at y++
    0x00,
    0x00,
    data_len,
    pixel
]

# clears bottom (landscape right) of each chip (each chip is 64x64 pixels)
cmd4 = [
    OUT_REPORT_DATA,
    0x01,  # chipsel | 1,
    0x00,
    0x00,
    data_len,
    pixel
]
canvas = None
def set_canvas_pixel(x, y):
    canvas.create_line(x, y, x+1, y, fill="#000")

def quit():
    global root
    root.destroy()

def fill():
    for y in range(p.dc["height"]):
        for x in range(p.dc["width"]):
            # if x < y:
            set_canvas_pixel(x, y)
            p.set_pixel(x, y, True)
            # else:
                # p.set_pixel(x, y, False)

def draw_pattern():
    for y in range(64):
        # y = 0
        # x = 32
        # if True:
        for x in range(128):
            set_canvas_pixel(x, y)
            p.set_pixel(x, y, True)

def draw_southwest_arrow():
    for y in range(64):
        for x in range(64):
            refresh_enable = False
            if x < y:
                set_canvas_pixel(x, y)
                p.set_pixel(x, y, True, refresh_enable=refresh_enable)
            # else:
                # p.set_pixel(x, y, False)
    # p.invalidate(zones=[0,1])  # was invalidated automatically anyway
    p.refresh()

count = 0
draw_enable = False
def getorigin(eventorigin):
    global x0,y0
    global count
    global draw_enable
    x0 = eventorigin.x
    y0 = eventorigin.y
    if draw_enable:
        set_canvas_pixel(x0, y0)
        p.set_pixel(x0, y0, True)
        # p.set_pixel(x0, y0, True)
        # p.set_pixel(x0, y0, True)
        count += 1
        print("[ testing ] " + str(count) + " getorigin "
              + str(x0) + "," + str(y0))

p = PicoLcd()
p.verbose_enable = True

print("Generating form")

root = tk.Tk()
# canvas = tk.Frame(root, width=p.dc["width"], height=p.dc["height"])
    # bd=0
# canvas.pack(expand=1, fill=tk.BOTH)
# canvas.pack_propagate(False)
canvas = tk.Canvas(root, width=p.dc["width"], height=p.dc["height"])
canvas.pack()
canvas.create_rectangle(0, 0, p.dc["width"], p.dc["height"],
    outline="WHITE", fill="WHITE")
    # outline="#fff", fill="#fff")

root.wm_title("picolcd testing by expertmm")
root.bind("<Button 1>", getorigin)

def enable_draw_click():
    global draw_enable
    draw_enable = True

draw_enable_btn = tk.Button(
    root,
    text="Enable Mouse Drawing\n(on blank above)",
    command=enable_draw_click)
draw_enable_btn.pack()

text_entry = tk.Entry(root)
text_entry.pack()

text_id = None

def render_text_click():
    global text_id
    text = text_entry.get()
    # NOTE: y sets the MIDDLE of the text
    x = 0
    y = 16
    # if text_id is None:
    text_id = canvas.create_text(
        x, y, anchor=tk.W,
        fill="#000",
        text=text)
        # font="Purisa"
    # else:
        # canvas.itemconfigure(text_id, text=text)
    p.draw_text(y, x, text)

render_text_btn = tk.Button(
    root,
    text="Render This Text\n(NOT YET IMPLEMENTED)",
    command=render_text_click)
render_text_btn.pack()

draw_arrow_btn = tk.Button(
    root,
    text="Draw arrow SW",
    command=draw_southwest_arrow)
draw_arrow_btn.pack()

max_byte_count = 13  # usually a command is 6 or 13 bytes
entries = []
for i in range(max_byte_count):
    e = tk.Entry(root)
    e.pack()
    entries.append(e)

run_btn = None

def load_cmd(cmd):
    global cmd_len
    cmd_len = len(cmd)
    run_btn["text"] = "Send " + str(len(cmd)) + " bytes"
    for i in range(len(entries)):
        e = entries[i]
        e.delete(0, tk.END)
        if i < len(cmd):
            these_bytes = bytes([cmd[i]])
            is_ok = True
            if len(these_bytes) > 1:
                for offset in range(3):
                    byte_i = offset + 1
                    if these_bytes[byte_i] > 0:
                        print("ERROR: " + str(cmd[i])
                              + " is too big for byte")
                        is_ok = False
                        break
            if is_ok:
                e.insert(0, binascii.hexlify(these_bytes[:1]))
            else:
                load_cmd(blank_cmd)
                break

def load_long_btn_click():
    load_cmd(cmd3)

def load_short_btn_click():
    load_cmd(cmd4)

def run_click():
    this_data_len = 1
    if cmd_len is not None:
        cmd = []
        is_ok = True
        for i in range(cmd_len):
            e = entries[i]
            # cmd.append(int(e.get()))
            these_bytes = bytearray.fromhex(e.get())
            if len(these_bytes) == 0:
                these_bytes = bytearray.fromhex("00")
            elif len(these_bytes) > 1:
                print("ERROR in run_click: " + e.get() + " is too big"
                      " for byte")
                is_ok = False
                break
            if i == cmd_len - 2:
                this_data_len = int(bytearray.fromhex(e.get())[0])
            cmd.append(these_bytes[0])
        this_hex_s = entries[cmd_len - 1].get()
        if len(this_hex_s) == 2:
            data_entry_byte = bytearray.fromhex(this_hex_s)[0]
            for data_count in range(this_data_len):
                cmd.append(data_entry_byte)
            if is_ok:
                p.wr(bytes(cmd))
        else:
            print("ERROR in run_cmd_click: '" + this_hex_s + "' at"
                  + " at index " + str(cmd_len-1) + " is not a byte.")
    else:
        print("ERROR in run_cmd_click: cmd_len is not known."
              " Load an example first.")

def clear_click():
    p.clear()
    canvas.create_rectangle(0, 0, p.dc["width"], p.dc["height"],
    outline="#fff", fill="#fff")

run_btn = tk.Button(root, text="Send 0 Bytes",
                      command=run_click)
run_btn.pack()
load_short_btn = tk.Button(root, text="Load 6-byte cmd",
                           command=load_short_btn_click)
load_short_btn.pack()
load_long_btn = tk.Button(root, text="Load 13-byte cmd",
                          command=load_long_btn_click)
load_long_btn.pack()
clear_btn = tk.Button(root, text="Clear LCD",
                      command=clear_click)
clear_btn.pack()
#main.mainloop()
#tk.mainloop()

# p.clear(val=0x00, data_len=32)
# p.clear(val=0x00)
# p.clear(val=0xFF, data_len=32, line_len=8, chip_count=4)
# data_len controls rightness (2 at a time--32 fills all 64)
# line_len controls downness (8 is all 64 since 1-bit graphics)
# chip_count controls which chip (there are 4 from left to right)
#
# p.clear(val=0x0F, data_len=32, line_len=8, chip_count=4)
# p.flash()
# p.backlight(128)
# clock:
# while True:
    # p.draw_text(3, 0, datetime.now().ctime()[:20])
    # time.sleep(0.5)
# p.set_pixel(4, 0, True)
# draw_southwest_arrow()
# draw_pattern()
# fill()
print("Loading form")

root.mainloop()

