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

# from pypicolcd import PicoLCD
# from pypicolcd import to_bool
# from pypicolcd import find_resource
# from pypicolcd import get_font_meta
from datetime import datetime
import random
import timeit
import pypicolcd
# from pypicolcd.lcddaemon import LCDDaemon
from pypicolcd.lcddaemon import LCD_PORT
from timeit import default_timer as best_timer
import sys
import json
import socket
import logging
import asyncore
import socket
import json
import urllib.parse
# TODO: gradually add features from example-cli.py

def customDie(msg, exit_code=1, logger=None):
    print("")
    print("")
    print("ERROR:")
    print(msg)
    print("")
    print("")
    exit(exit_code)

class HTTPClient(asyncore.dispatcher):

    def __init__(self, host, path, action):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = LCD_PORT
        self.connect( (host, LCD_PORT) )
        buffer_s = 'GET {} HTTP/1.0\r\n\r\n'.format(path)
        self.buffer = buffer_s.encode()
        # self.buffer2 = json.dumps(action).encode()
        # try:
        # except ConnectionRefusedError:
            # print("* the lcd-daemon is not running.")
            # self.close()
            # return

    def handle_connect(self):
        pass

    def handle_error(self):
        print("* lcd-daemon is not running or is otherwise"
              " inaccessible at {}:{}.".format(self.host, self.port))
        self.close()  # ONLY close on read in one-shot command scripts.

    def handle_close(self):
        self.close()
        # print("* the connection has closed.")

    def handle_read(self):
        # print(self.recv(pypicolcd.JSON_MAX).decode())

        res_bytes = self.recv(pypicolcd.JSON_MAX)
        if res_bytes:
            res_s = res_bytes.decode()
            try:
                res = json.loads(res_s)
                print("* the server says: {}".format(res))
                code = 0
                if res.get("error") is not None:
                    code = 1
            except json.decoder.JSONDecodeError:
                print("* ERROR: the server provided invalid JSON:"
                      " '{}'".format(res_s))
        else:
            print("* ERROR: The server provided an empty response.")
        self.close()  # ONLY close on read in one-shot command scripts.

    def writable(self):
        return (len(self.buffer) > 0)

    def handle_write(self):
        sent = self.send(self.buffer)
        # print("* sent '{}'".format(self.buffer[:sent].decode()))
        self.buffer = self.buffer[sent:]

def main():
    logger = logging.getLogger("lcd-cli")
    # lcdd = LCDDaemon()
    action = {}
    lines = []
    if len(sys.argv) < 1:
        sys.stdout.write("You didn't provide any parameters, so there is nothing to do.")
        return 1
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
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
    # lcdd.push_action(action)

    # s = socket.socket()
    # s.connect(('127.0.0.1', LCD_PORT))
    # # while True:
    # s.send(json.dumps(action).encode());
    # # if(str == "Bye" or str == "bye"):
        # # break
    # res = None
    # res_bytes = s.recv(pypicolcd.JSON_MAX)
    # if res_bytes:
        # res_s = res_bytes.decode()
        # try:
            # res = json.loads(res_s)
            # print("* the server says: {}".format(res))
        # except json.decoder.JSONDecodeError:
            # print("* ERROR: the server provided invalid JSON:"
                  # " '{}'".format(res_s))
    # else:
        # print("* ERROR: The server provided an empty response.")
    # s.close()
    action_json = json.dumps(action)
    url_args = ""
    url_args = "?json=" + urllib.parse.quote(action_json, safe='')

    client = HTTPClient('localhost', '/'+url_args, action)
    asyncore.loop()

if __name__ == "__main__":
    main()

