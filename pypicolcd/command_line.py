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
from datetime import datetime
import random
import timeit
from timeit import default_timer as best_timer
import sys

# TODO: gradually add features from example-cli.py

def customDie(msg, exit_code=1):
    print("")
    print("")
    print("ERROR:")
    print(msg)
    print("")
    print("")
    exit(exit_code)
_LINES_MAX = 4


def show_image(path, params={}, destination=None):
    p = destination
    if p is None:
        p = PicoLCD()
    if not os.path.isfile(image_path):
        raise ValueError("{} does not exist.".format(image_path))
    p.draw_image((x, y), image_path, brightness=1)
    return p

def show_lines(lines, params={}, destination=None):
    p = destination
    if p is None:
        p = PicoLCD()
    if p.dc is None:
        error = p.error
        if error is None:
            raise RuntimeError("ERROR: could not load device for unknown reason.")
        # else error already shown by p

    if params.get("clear") is True:
        p.clear()
    # lines = params.get("lines")
    if lines is None:
        lines = []
    x, y = 0, -1
    for line in lines:
        if len(lines) < _LINES_MAX:
            y += 1
            # p_dfs = p.default_font_size
            # p.draw_text(y, x,
                        # "Default font is " + str(p_dfs) + "pt ninepin")

            PicoLCD.find_font("Press Start")
            p.draw_text(y, x, "\"Press Start\" font",
                        font_path="fonts/prstartk.ttf", font_size=6,
                        erase_behind_enable=True)
            print("Your LCD should now show info about included fonts"
                  " which are available on graphics type picoLCD models.")
        else:
            customDie("Only {} line(s) fit(s) on the LCD--skipping '{}'.".format(_LINES_MAX, arg))
    return p


def main():
    settings = {}
    lines = []
    allowed_names = ["background", "foreground"]
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if arg.startswith("--"):
            if (len(arg) == 2):
                customDie("There was a blank argument")
            arg_parts = arg.split("=")
            arg_n = arg_parts[0]
            arg_v = None
            if len(arg_parts) > 1:
                arg_v = arg_parts[1]
                # settings[arg_n] = arg_v
                if len(argv) == 0:
                    customDie("There was a blank value: " + arg)
            else:
                settings[arg_n] = True

            if len(arg_parts) > 2:
                customDie("There was more than one '=' in {}".format(arg))
            if arg_n == "clear":
                settings[arg_n] = PicoLCD.to_bool(arg_v)
            elif arg_n in allowed_names:
                settings[arg_n] = arg_v
            else:
                customDie("{} is an unknown option.".format(arg))
        else:
            lines.append(arg)
    p = PicoLCD()

    if settings.get("clear") is True:
        p.clear()

    image_path = settings.get("foreground")

    if image_path is not None:
        show_image(image_path, destination=p)

    show_lines(lines, params=settings, destination=p)

    image_path = settings.get("foreground")
    if image_path is not None:
        show_image(image_path, destination=p)


if __name__ == "__main__":
    main()

