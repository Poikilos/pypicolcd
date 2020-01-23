#!/usr/bin/env python3
"""
This is a CLI for pypicolcd, which is a module for driverless writing to
picoLCD
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

from pypicolcd import lcdclient

import sys
import logging


def customDie(msg, exit_code=1, logger=None):
    print("")
    print("")
    print("ERROR:")
    print(msg)
    print("")
    print("")
    exit(exit_code)


def run(args):
    logger = logging.getLogger("lcd-cli")
    # lfbs = LCDFramebufferServer()
    action = {}
    lines = []
    if len(args) < 1:
        sys.stdout.write("You didn't provide any parameters, so there"
                         " is nothing to do.")
        return 1
    for i in range(1, len(args)):
        arg = args[i]
        if arg.startswith("--") and not arg.startswith("---"):
            if (len(arg) == 2):
                customDie("There was a blank argument", logger=logger)
            arg_parts = arg[2:].split("=")
            name = arg_parts[0]
            value = None
            if len(arg_parts) > 1:
                value = arg_parts[1]
                action[name] = value
                if len(value) == 0:
                    customDie("There was a blank value: " + arg,
                              logger=logger)
            else:
                action[name] = True
                value = True

            if len(arg_parts) > 2:
                customDie(
                    "There was more than one '=' in {}".format(arg),
                    logger=logger
                )
        else:
            lines.append(arg)
    if len(lines) > 0:
        action["lines"] = lines
    # lfbs.push_action(action)

    # s = socket.socket()
    # s.connect(('127.0.0.1', LCD_PORT))
    # # while True:
    # s.send(json.dumps(action).encode());
    # # if(str == "Bye" or str == "bye"):
    #     # break
    # res = None
    # res_bytes = s.recv(pypicolcd.JSON_MAX)
    # if res_bytes:
    #     res_s = res_bytes.decode()
    #     try:
    #         res = json.loads(res_s)
    #         print("* the server says: {}".format(res))
    #     except json.decoder.JSONDecodeError:
    #         print("* ERROR: the server provided invalid JSON:"
    #               " '{}'".format(res_s))
    # else:
    #     print("* ERROR: The server provided an empty response.")
    # s.close()

    return lcdclient.send_action(action)


def main():
    results = run(sys.argv)
    if results.get("status") != "OK":
        print("* {}".format(results))
        return 1
    else:
        print('* The server responded with: {}'.format(results))
    return 0


if __name__ == "__main__":
    # NOTE: You can't return anything, since you can't return outside
    # of a function.
    main()
