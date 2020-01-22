#!/usr/bin/env python3
"""
pypicolcd, a module for driverless writing to picoLCD
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


import pypicolcd
from pypicolcd import PicoLCD
# from pypicolcd import find_resource
from pypicolcd import get_font_meta
from pypicolcd import to_bool

import sys
import signal
import logging
import json
import asyncore
import socket
try:
    from urllib.parse import unquote
    from urllib.parse import quote
except ImportError:
    from urlparse import unquote
    from urllib import quote
from datetime import datetime
try:
    import systemd.daemon
except ImportError:
    # NOTE: ModuleNotFoundError is only available in Python 3.
    pass

LCD_PORT = 25664


def customDie(msg, exit_code=1, logger=None):
    print("")
    print("")
    print("ERROR:")
    print(msg)
    print("")
    print("")
    exit(exit_code)


class LCDRequestHandler(asyncore.dispatcher_with_send):
    def __init__(self, sock, service):
        asyncore.dispatcher_with_send.__init__(self, sock)
        self.service = service

    # See https://docs.python.org/2/library/asyncore.html
    def handle_read(self):
        req_bytes = self.recv(pypicolcd.JSON_MAX)
        if req_bytes is not None:
            req_s = req_bytes.decode()
            if len(req_s) > 0:
                if req_s.startswith("GET /"):
                    self.reroute_get(req_s)
                else:
                    print("* the request type is not implemented:"
                          " '{}'".format(req_s))
            else:
                pass
                # TODO: I'm not sure why this happens, but it happens
                #   whenever the connection closes.
                # print("* the client provided a blank get request.")
        else:
            print("* the client provided a NULL get request.")

    def reroute_get(self, req_s):
        if req_s.startswith("GET /"):
            words = req_s.split(" ")
            # print("* got request parts: {}".format(words))
            url_path = words[1]
            # print("* url_path:'{}'".format(url_path))
            mark_i = url_path.find("?")
            params_s = ""
            if mark_i >= 0:
                params_s = url_path[mark_i+1:]
                url_path = url_path[:mark_i]
            # else:
            #     print("* there are no params in the path.")
            # if len(params_s) < 1:
            #     print("* WARNING: url_path's ? is at"
            #           " {}".format(mark_i))
            #     print("* WARNING: and {} is at 2".format(url_path[2]))
            # print("* as '{}'".format(params_s))
            chunks = params_s.split("&")
            params = {}
            for chunk in chunks:
                parts = chunk.split("=")
                name = None
                value = None
                # print("  * contains '{}'".format(chunk))
                if len(parts) >= 1:
                    name = parts[0]
                if len(parts) >= 2:
                    value = unquote(parts[1])
                if len(parts) > 2:
                    print("  * ERROR: malformed URL param:"
                          " '{}'".format(chunk))
                # print("    * as {}:'{}'".format(name, value))
                if name == 'json':
                    try:
                        req = json.loads(value)
                        res = self.service.push_action(req)
                        # print("* The server got a JSON object:"
                        #       " {}".format(req))
                        res_bytes = json.dumps(res).encode()
                        self.send(res_bytes)
                    except json.decoder.JSONDecodeError:
                        msg = ("The client provided invalid json:"
                               " json='{}'".format(value))
                        print("  * ERROR: " + msg)
                        res = {"error": msg}
                        res_bytes = json.dumps(res).encode()
                        self.send(res_bytes)
                    except pypicolcd.DisconnectedError:
                        msg = ("No known picoLCD USB device is"
                               " connected to the server.")
                        # print("* ERROR: {}".format(msg))
                        # NOTE: push_action usually shows the error
                        res = {"error": msg}
                        res_bytes = json.dumps(res).encode()
                        self.send(res_bytes)
                    except ValueError as e:
                        msg = str(e)
                        res = {"error": msg}
                        res_bytes = json.dumps(res).encode()
                        self.send(res_bytes)
                else:
                    params[name] = value
            # try:
            #     req = json.loads(req_s)
            #     res = self.service.push_action(req)
            #     res_bytes = json.dumps(res).encode()
            #     self.send(res_bytes)
            # except json.decoder.JSONDecodeError:
            #     print("* the client provided invalid json:"
            #           " '{}'".format(req_s))
        else:
            raise ValueError("reroute_get can only handle strings"
                             " starting with 'GET /'")


# See https://docs.python.org/2/library/asyncore.html
class LCDServer(asyncore.dispatcher):
    def __init__(self, host, port, service):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        print("* lcd-fb is listening on {}:{}".format(host, port))
        self.service = service
        try:
            systemd.daemon.notify('READY=1')
        except NameError:
            # The systemd module did not import.
            pass

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            now = datetime.now()
            now_s = now.strftime("%Y-%m-%d %H:%M:%S")
            sock, addr = pair
            print("{}: Incoming connection from"
                  " {}".format(now_s, repr(addr)))
            handler = LCDRequestHandler(sock, self.service)


class LCDFramebufferServer(asyncore.dispatcher_with_send):
    p = None

    def __init__(self, logger=None):
        self.p = PicoLCD()
        if logger is None:
            logging.getLogger('lcd-fb')
        else:
            self.logger = logger

    def show_lines(self, lines, font=None, x=0, y=0):
        shown_count = 0
        # if not self.p.ready():
        if self.p.dc is None:
            error = self.p.error
            if error is None:
                raise RuntimeError("ERROR: could not load device for"
                                   " an unknown reason.")
            else:
                # error already shown by self.p
                return False

        if lines is None:
            lines = []
        if (x is None):
            x = 0
        else:
            x = int(x)
        if (y is None):
            y = 0
        else:
            y = int(y)
        # font = "Press Start"
        if font is None:
            font = self.p.default_font
        meta = get_font_meta(font)
        if meta is None:
            raise RuntimeError("ERROR: '{}' was not"
                               " found.".format(font))
        _LINES_MAX = self.p.get_height() // (meta["default_size"] + 1)
        for line in lines:
            row = y // 8
            if row < _LINES_MAX:
                # p_dfs = self.p.default_font_size
                # self.p.draw_text(
                #     y,
                #     x,
                #     "Default font is " + str(p_dfs) + "pt ninepin"
                # )
                if line is None:
                    raise ValueError("line is None")
                print("* showing '{}'...".format(line))
                self.p.draw_text_at((x, y), line, font=font,
                                    erase_behind_enable=True)
                shown_count += 1
                y += 8
            else:
                raise ValueError("* Only {} line(s) fit(s) on the LCD,"
                                 " so '{}' will not"
                                 " appear.".format(_LINES_MAX, line))
        # print("* show_lines is complete. The LCD should have"
        #       " {} lines.".format(shown_count))

    def show_image(self, path):
        if not os.path.isfile(image_path):
            raise ValueError("{} does not exist.".format(image_path))
        self.p.draw_image((x, y), image_path, brightness=1)

    def push_action(self, action):
        """
        Process an action dictionary, such as URL params or command line
        params, in either case reduced to names and values.
        """
        prev_verbose = self.p.verbose_enable
        res = {}
        lines = action.get("lines")
        allowed_names = ["background", "foreground", "brightness",
                         "lines", "verbose", "font", "x", "y"]
        allowed_commands = ["clear", "flash", "push"]
        for name, value in action.items():
            if name in allowed_names:
                if name == "verbose":
                    self.p.verbose_enable = to_bool(value)
                else:
                    action[name] = value
            elif name in allowed_commands:
                action[name] = True
            else:
                self.p.verbose_enable = prev_verbose
                raise ValueError("{} is an unknown option (value"
                                 " '{}').".format(name, value))

        font = action.get("font")
        if font is not None:
            meta = get_font_meta(font)
            if meta is None:
                raise ValueError("The font is not known. Try (case"
                                 " doesn't matter):"
                                 " {}".format(font_meta.keys()))

        if action.get("clear") is True:
            self.p.clear()

        brightness = action.get("brightness")
        if brightness is not None:
            b = int(brightness)
            # print("* setting brightness to {}...".format(b))
            self.p.set_backlight(b)

        image_path = action.get("foreground")
        x = action.get("x")
        y = action.get("y")
        if image_path is not None:
            self.show_image(image_path)
        if action.get("push") is True:
            if (x is not None) or (y is not None):
                raise ValueError("x and y cannot be set along with the"
                                 " push option, since push uses control"
                                 " characters and scrolls"
                                 " automatically")
            if font is not None:
                raise ValueError("Custom fonts do not work with push,"
                                 " since it requires a fixed line"
                                 " height (that is an even divisor of"
                                 " the device height; only 8 is"
                                 " implemented).")
            try:
                if lines is not None:
                    all_text = " ".join(lines)
                    print("* showing {}...".format(all_text))
                    self.p.push_text(all_text)
                    # for line in lines:
                    #     self.p.push_text(line)
            except pypicolcd.DisconnectedError as e:
                print("  * {}".format(e))
        else:
            self.show_lines(lines, font=font, x=x, y=y)

        image_path = action.get("foreground")
        if image_path is not None:
            self.show_image(image_path)

        if action.get("flash") is True:
            self.p.flash()
            self.p.flash()

        res["info"] = "OK"
        self.p.verbose_enable = prev_verbose
        return res

    def handle_signal(self, signum, frame):
        msg = "lcd-fb got signal {}.".format(signum)
        if signum == 15:
            msg = "lcd-fb got signal {} (terminate)".format(signum)
        self.p.draw_text(1, 1, msg)
        now = datetime.now()
        now_s = now.strftime("%Y-%m-%d %H:%M:%S")
        self.p.draw_text(2, 1, "@" + now_s)
        logging.info('Exited')


def main():
    logger = logging.getLogger('lcd-fb')
    action = {}
    lines = []
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
                    customDie(
                        "There was a blank value: " + arg,
                        logger=logger
                    )
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
    lcdd = LCDFramebufferServer(logger=logger)

    # See <https://raspberrypi.stackexchange.com/questions/77738/
    # how-to-exit-a-python-daemon-cleanly>
    signal.signal(signal.SIGTERM, lcdd.handle_signal)

    host = action.get("localhost")
    if host is None:
        host = 'localhost'
    else:
        del action["localhost"]
        print("* running as host '{}'".format(host))
    lcdd.push_action(action)

    # See https://docs.python.org/2/library/asyncore.html
    server = LCDServer(host, LCD_PORT, lcdd)
    asyncore.loop()

    # Ignore code below, and use the asynccore subclass above instead.
    # See [Nischaya Sharma's Nov 29, 2018 answer edited Feb 16, 2019 by
    # Mohammad Mahjoub](https://stackoverflow.com/a/53536336)
    # on
    # <https://stackoverflow.com/questions/21233340/
    # sending-string-via-socket-python>
    # s = socket.socket()
    # try:
    #     s.bind(('', LCD_PORT))
    # except OSError as e:
    #     print(e)
    #     print("Try:")
    #     print("sudo fuser -k {}/tcp".format(LCD_PORT))
    #     exit(1)
    # s.listen(5)
    # c, addr = s.accept()
    # print("Socket Up and running with a connection from"
    #       " {}".format(addr))
    # while True:
    #     rcvdData = c.recv(1024).decode()
    #     print("* got '{}'".format(rcvdData))
    #     # print "S:",rcvdData
    #     # sendData = raw_input("N: ")
    #     req = json.loads(rcvdData)
    #     lcdd.push_action(req)
    #     res = {}
    #     res["info"] = "ok"
    #     c.send(json.dumps(res).encode())
    #     # if (sendData == "Bye" or sendData == "bye"):
    #         # break
    # c.close()


if __name__ == "__main__":
    main()
