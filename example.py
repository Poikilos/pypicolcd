#!/bin/env python3
from picolcd import PicoLcd
from datetime import datetime
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

p = PicoLcd()

# p.set_pixel((0, 0), False, force_refresh_enable=True)
# NOTE: if you try to do p.set_pixel((0, 0), False) before True,
# and LCD was already displaying a pixel from a previous session,
# Nothing will be done since framebuffer is not loaded from chip
# but generated on creation of PicoLcd class (unless
# you pass force_refresh_enable=True to set_pixel)

p.clear()
p.verbose_enable = True
p.set_pixel((0, 0), True)
x, y = 0, 0
# p.draw_image((x, y), "images/maze.png")
# p.draw_image((x, y), "images/qbist.png", brightness=20)
# p.draw_image((x, y), "images/gradient-vertical.png", threshold=float(30./255.))
# p.draw_image((x, y), "images/gradient-vertical.png", brightness=1)
p.draw_image((x, y), "images/checker-gradient.png", brightness=1)
# NOTE: draw_text uses row,col format which is y,x order
x, y = 0, 0
p_dfs = p.default_font_size
p.draw_text(y, x,
            "Default font is " + str(p_dfs) + "pt ninepin")

x, y = 0, 1
# p.draw_text(y, x, "Zephyrean works if tiny ",
            # font_path="fonts/zephyreg.ttf",  # reg is illegible small
            # font_size=7, threshold=.5)
p.draw_text(y, x, "Zephyrean is smallest 8pt readable font",
            font_path="fonts/zephyrea.ttf",
            font_size=8, threshold=.5)
x, y = 0, 2
p.draw_text(y, x, "Flottflott font is unreadable below font size 11",
            font_path="fonts/Flottflott.ttf",
            font_size=11, threshold=.5, erase_behind_enable=True)
x, y = 0, 3
p.draw_text(y, x, "Press Start is the name of this font",
            font_path="fonts/prstartk.ttf", font_size=6,
            erase_behind_enable=True)
print("Your LCD should now show info about included fonts"
      " which are available on graphics type picoLCD models.")
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
count = 0
max_count = 1000
print("Press Ctrl C to exit. Drawing "
      + str(max_count) + " animation frames(s)...")
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
    print(str(count))

