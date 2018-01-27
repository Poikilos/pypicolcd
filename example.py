#!/bin/env python3
from picolcd import PicoLcd
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

# p.set_pixel(0, 0, False, force_refresh_enable=True)
# NOTE: if you try to do p.set_pixel(0, 0, False) before True,
# and LCD was already displaying a pixel from a previous session,
# Nothing will be done since framebuffer is not loaded from chip
# but generated on creation of PicoLcd class (unless
# you pass force_refresh_enable=True to set_pixel)

p.clear()
p.verbose_enable = True
p.set_pixel(0, 0, True)
x, y = 0, 0
p.draw_image((x, y), "maze.png")
# NOTE: draw_text uses row,col format which is y,x order
x, y = 0, 16
p.draw_text(y, x, "Hello World!")
x, y = 0, 48
p.draw_text(y, x, "Alpha monkey has the banana.")

