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
from pypicolcd import to_bool
# from pypicolcd import find_resource
from pypicolcd import get_font_meta
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



def show_image(path, params={}, destination=None):
    p = destination
    if p is None:
        p = PicoLCD()
    if not os.path.isfile(image_path):
        raise ValueError("{} does not exist.".format(image_path))
    p.draw_image((x, y), image_path, brightness=1)
    return p

def show_lines(lines, params={}, destination=None):
    shown_count = 0
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
    meta = get_font_meta("Press Start")
    _LINES_MAX = p.get_height() // (meta["default_size"] + 1)
    for line in lines:
        if y < _LINES_MAX:
            y += 1
            # p_dfs = p.default_font_size
            # p.draw_text(y, x,
                        # "Default font is " + str(p_dfs) + "pt ninepin")
            if line is None:
                raise ValueError("line is None")
            print("* showing '{}'...".format(line))
            p.draw_text(y, x, line, font="Press Start",
                        erase_behind_enable=True)
            shown_count += 1
        else:
            customDie("* Only {} line(s) fit(s) on the LCD, so '{}'"
                      " will not appear.".format(_LINES_MAX, line))
    # print("* show_lines is complete. The LCD should have"
          # " {} lines.".format(shown_count))
    return p

def main():
    settings = {}
    lines = []
    allowed_names = ["background", "foreground", "brightness"]
    allowed_commands = ["clear", "flash", "push"]
    if len(sys.argv) < 1:
        sys.stdout.write("You didn't provide any parameters, so there is nothing to do.")
        return 1
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if arg.startswith("--"):
            if (len(arg) == 2):
                customDie("There was a blank argument")
            arg_parts = arg[2:].split("=")
            name = arg_parts[0]
            value = None
            if len(arg_parts) > 1:
                value = arg_parts[1]
                # settings[name] = value
                if len(value) == 0:
                    customDie("There was a blank value: " + arg)
            else:
                # settings[name] = True
                value = True

            if len(arg_parts) > 2:
                customDie("There was more than one '=' in {}".format(arg))
            if name == "clear":
                settings[name] = to_bool(value)
            elif name in allowed_names:
                settings[name] = value
            elif name in allowed_commands:
                settings[name] = True
            else:
                customDie("{} is an unknown option (name '{}', value '{}').".format(arg, name, value))
        else:
            lines.append(arg)
    p = PicoLCD()

    if settings.get("clear") is True:
        p.clear()

    brightness = settings.get("brightness")
    if brightness is not None:
        b = int(brightness)
        print("* setting brightness to {}...".format(b))
        p.set_backlight(b)

    image_path = settings.get("foreground")

    if image_path is not None:
        show_image(image_path, destination=p)

    if settings.get("push") is True:
        for line in lines:
            p.push_text(line + " ")
    else:
        show_lines(lines, params=settings, destination=p)

    image_path = settings.get("foreground")
    if image_path is not None:
        show_image(image_path, destination=p)

    if settings.get("flash") is True:
        p.flash()
        p.flash()
        p.flash()

if __name__ == "__main__":
    main()

