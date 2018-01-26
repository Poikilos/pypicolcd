from picolcd import PicoLcd
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
p.draw_text(0, 16, "Hello World!")
p.draw_text(0, 48, "Alpha monkey has the banana.")

