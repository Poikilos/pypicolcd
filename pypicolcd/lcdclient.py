#!/usr/bin/env python
# from pypicolcd import PicoLCD
# from pypicolcd import to_bool
# from pypicolcd import find_resource
# from pypicolcd import get_font_meta
# from datetime import datetime
# import random
import pypicolcd
# from pypicolcd.lcddaemon import LCDFramebufferServer
from pypicolcd.lcdframebuffer import LCD_PORT
# import timeit
# from timeit import default_timer as best_timer
import sys
import json
import socket
import asyncore
import copy
try:
    from urllib.parse import urlparse
    from urllib.parse import quote
except ImportError:
    from urlparse import urlparse
    from urllib import quote
# TODO: gradually add features from example-cli.py


class LCDFramebufferClient(asyncore.dispatcher):

    def __init__(self, host, path, action, port=None, results=None):
        """
        Initialize a temporary one-action client (that closes after
        sending an object to a pypicolcd lcd-fb server and showing
        the response).

        Sequential arguments:
        host -- Connect to this hostname or IP address.
        path -- Connect to this path on the server (normally /)
        action -- Send this object as JSON to the server.

        Keyword arguments:
        port -- Use this port on the remote machine (if None, default
            to pypicolcd.lcdframebuffer.LCD_PORT)
        results -- The object will use this dictionary for output:
            either response variables that the server sends as JSON, or
            an "error" key generated locally. The server may also
            generate an "error" key. Only if the response is good, the
            results will contain a "status" key with the string "OK".
            This parameter sets the self.results member.
        """
        self.results = results
        if port is None:
            port = LCD_PORT
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.connect((host, port))
        buffer_s = 'GET {} HTTP/1.0\r\n\r\n'.format(path)
        self.buffer = buffer_s.encode()
        # self.buffer2 = json.dumps(action).encode()
        # try:
        # except ConnectionRefusedError:
        #     print("* the lcd-fb server is not running.")
        #     self.close()
        #     return

    def handle_connect(self):
        pass

    def handle_error(self):
        # See
        # https://github.com/python/cpython/blob/master/Lib/asyncore.py
        # nil, t, v, tbinfo = compact_traceback()
        # See <https://github.com/python/cpython/blob/
        # 5bbac8cbdf140ebce446ea4e7db2b20a5d7b8402/Lib/asyncore.py#L533>
        t, v, tb = sys.exc_info()

        msg = (
            "lcd-fb at {}:{} responded with {}:{}.".format(
                self.host,
                self.port,
                t,
                v
            )
        )
        if self.results is not None:
            self.results["error"] = msg
        else:
            print("ERROR: " + msg)
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
                if self.results is not None:
                    for k, v in res.items():
                        self.results[k] = v
                else:
                    print("* the server says: {}".format(res))
                # code = 0
                # if res.get("error") is not None:
                    # code = 1
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


def send_action(action):
    """
    Send a dictionary to the server as JSON using a single-use
    LCDFramebufferClient instance.

    Sequential arguments:
    action -- a dictionary containing settings such as:
        - lines: a list of custom text lines
        - host: the hostname or IP address of the server
        - port: the port of the server
        - help: set this to True to see a list of commands.
    """
    action = copy.deepcopy(action)
    # action = json.loads(json.dumps(action))
    # deepcopy is not thread safe and json is, according to
    # <https://stackoverflow.com/questions/5105517/
    # deep-copy-of-a-dict-in-python#comment71372193_5105554>
    host = action.get("host")
    if host is None:
        host = "localhost"
    if "host" in action:
        del action["host"]
    print("* sending '{}'...".format(action))
    action_json = json.dumps(action)
    url_args = ""
    url_args = "?json=" + quote(action_json, safe='')
    # print("* sending '{}'...".format(url_args))
    port = action.get("port")
    if "port" in action:
        del action["port"]
    results = {}
    client = LCDFramebufferClient(host, '/'+url_args, action, port=port,
                                  results=results)
    asyncore.loop()
    return results
