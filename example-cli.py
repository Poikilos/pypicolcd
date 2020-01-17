#!/usr/bin/env python3
# (example for) pypicolcd, a module for driverless writing to picoLCD
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

from pypicolcd import PicoLCD
from pypicolcd import font_meta
from pypicolcd import get_font_meta
from pypicolcd import find_resource
from datetime import datetime
import random
import timeit
from timeit import default_timer as best_timer
import sys

p = PicoLCD()
if p.dc is None:
    error = p.error
    if error is None:
        error = "ERROR: could not load device for unknown reason."
        print(error)
    # else error already shown by p
    exit(1)
# p.set_pixel((0, 0), False, force_refresh_enable=True)
# NOTE: if you try to do p.set_pixel((0, 0), False) before True,
# and LCD was already displaying a pixel from a previous session,
# Nothing will be done since framebuffer is not loaded from chip
# but generated on creation of PicoLCD class (unless
# you pass force_refresh_enable=True to set_pixel)

p.clear()
print("* cleared")
p.verbose_enable = True
print("* p.verbose_enable is " + str(p.verbose_enable))
p.set_pixel((0, 0), True)
x, y = 0, 0
# p.draw_image((x, y), find_resource("images/maze.png"))
# p.draw_image((x, y), find_resource("images/qbist.png"), brightness=20)
# p.draw_image((x, y), find_resource("images/gradient-vertical.png"), threshold=float(30./255.))
# p.draw_image((x, y), find_resource("images/gradient-vertical.png"), brightness=1)
p.draw_image((x, y), find_resource("images/checker-gradient.png"), brightness=1)
# NOTE: draw_text uses row,col format which is y,x order
x = 0

try_fonts = [None, "Zephyrean", "Flottflott", "Press Start"]
p_dfs = p.default_font_size
p_df = p.default_font
for font_i in range(min(len(try_fonts), 4)):
    name = try_fonts[font_i]
    msg = None
    meta = None
    threshold = .5
    erase_behind_enable = False
    if name is None:
        name = p_df
        threshold =  None
        meta = get_font_meta(name)
        msg = "The default font is {}pt {}.".format(p_dfs, name.title())
    else:
        meta = get_font_meta(name)
        msg = "\"{}\": {}".format(name, meta["note"])
    print("* showing {}...".format(name))
    if name == "Flottflott":
        erase_behind_enable = True
        pass
    if threshold is not None:
        p.draw_text(y, x, msg, font_path=meta["path"],
                    font_size=meta["default_size"], threshold=.5,
                    erase_behind_enable=erase_behind_enable)
    else:
        p.draw_text(y, x, msg, font_path=meta["path"],
                    font_size=meta["default_size"],
                    erase_behind_enable=erase_behind_enable)
    y += 1

print("* Your LCD should now show info about included fonts\n"
      "  which are available on graphics type picoLCD models.")
x, y = 211, 1
outline = ((x, y), (x+45, y+13))
p.draw_rect(outline, True, filled=False)
inner_rect = p.smaller_rect(outline)
x, y = inner_rect[0]
p.draw_text_at((x+1,y+2), datetime.now().ctime()[11:20], erase_rect=inner_rect)
x_vel = 1
y_vel = 1
im_w = 8
im_h = 8
r = x + im_w
b = y + im_h
x, y = 128, 64-im_h
max_count = 120
_fps_last_frame_tick = None
_fps_accumulated_time = 0.
_fps_accumulated_count = 0
last_update_s = None
fps = None

count = 0
print("* Press Ctrl C to exit. Drawing "
      + str(max_count) + " animation frames(s)...")
prev_done = None
sys.stderr.write("\n")
while count < max_count:
    # p.draw_rect(((x, y), (r, b)), False, filled=False)
        # erase old copy (slow, lots of flicker)
    x += x_vel
    y += y_vel
    r = x + im_w
    b = y + im_h
    p.draw_rect(((x, y), (r, b)), True, filled=False)
    if r + x_vel >= p.dc["width"]:
        x_vel = -x_vel
    elif x + x_vel < 0:
        x_vel = -x_vel
    if b + y_vel >= p.dc["height"]:
        y_vel = -y_vel
    elif y + y_vel < 0:
        y_vel = -y_vel
    count += 1
    done = float(count) / float(max_count)
    # print(str(count))
    # if (prev_done is None) or (done - prev_done > .1):
    sys.stderr.write("\r{:.0f}% ({} of {}): The square should be drawing over the LCD screen.".format(done * 100.0, count, max_count))
    prev_done = done
sys.stderr.write("\n")

count = 0
p.clear()
print("Press Ctrl C to exit. Drawing "
      + str(max_count) + " random number(s)...")
while count < max_count:
    n = random.randrange(10)
    p.push_text(str(n))
    count += 1
    fps = p.generate_fps()  # only gets fps at interval set by
                            # set_fps_interval, otherwise None
    # fps = p.get_fps()  # always gets fps if has ever been calculated
    if fps is not None:
        # print("[ example.py ] fps: " + str(fps))
        p.draw_text(0, 0, "fps: " + str(fps), erase_behind_enable=true)

