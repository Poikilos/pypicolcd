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
p.draw_text(
    y, x,
    "Default font is " + str(p.default_font_size) + "pt ninepin")
x, y = 0, 16
p.draw_text(y, x, "Flottflott font is unreadable below font size 11",
            font_path="fonts/Flottflott.ttf",
            font_size=11, threshold=.5, erase_behind_enable=True)
x, y = 0, 32
p.draw_text(y, x, "Press Start is the name of this font",
            font_path="fonts/prstartk.ttf", font_size=7,
            erase_behind_enable=True)
outline = ((192,8),(240,22))
p.draw_rect(outline, True, filled=False)
inner_rect = p.shrunken_rect(outline)
x, y = inner_rect[0]
p.draw_text(y+3, x+1, datetime.now().ctime()[11:20], erase_rect=inner_rect)
