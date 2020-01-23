#!/usr/bin/env python3
from pypicolcd import lcdclient

import os
import sys
import platform
import copy
from datetime import datetime
from pypicolcd.lcdframebuffer import get_commands
from pypicolcd.lcdframebuffer import get_bool_options
from pypicolcd import to_bool

_MAX_LINES = 4


class FreeMemLinux(object):
    """
    This is a non-cross platform way to get free memory on GNU+Linux
    systems. Note that this code uses the `with ... as`, which is
    conditionally Python 2.5 compatible! If for some reason you still
    have Python 2.5 on your system add in the head of your code, before
    all imports: from __future__ import with_statement

    according to [Oz123's answer](https://stackoverflow.com/a/24186720)
    Jun 12, 2014 (edited Oct 7, 2016; accessed Jan 14, 2020)
    on <https://stackoverflow.com/questions/17718449/
    determine-free-ram-in-python>
    """

    def __init__(self, unit='kB'):

        with open('/proc/meminfo', 'r') as mem:
            lines = mem.readlines()

        self._tot = int(lines[0].split()[1])
        self._free = int(lines[1].split()[1])
        self._buff = int(lines[2].split()[1])
        self._cached = int(lines[3].split()[1])
        self._shared = int(lines[20].split()[1])
        self._swapt = int(lines[14].split()[1])
        self._swapf = int(lines[15].split()[1])
        self._swapu = self._swapt - self._swapf

        self.unit = unit
        self._convert = self._factor()

    def _factor(self):
        """determine the convertion factor"""
        if self.unit == 'bytes':
            return 1
        if self.unit.lower() == 'kb':
            return 1024
        if self.unit.lower() == 'k':
            return 1024.0
        if self.unit.lower() == 'mb':
            return 1/1024.0
        if self.unit.lower() == 'm':
            return 1/1024.0
        if self.unit.lower() == 'gb':
            return 1/1024.0/1024.0
        if self.unit.lower() == 'g':
            return 1/1024.0/1024.0
        if self.unit == '%':
            return 1.0/self._tot
        else:
            raise Exception("Unit not understood")

    @property
    def total(self):
        return self._convert * self._tot

    @property
    def used(self):
        return self._convert * (self._tot - self._free)

    @property
    def used_real(self):
        """memory used which is not cache or buffers"""
        return self._convert * (self._tot - self._free -
                                self._buff - self._cached)

    @property
    def shared(self):
        return self._convert * (self._tot - self._free)

    @property
    def buffers(self):
        return self._convert * (self._buff)

    @property
    def cached(self):
        return self._convert * self._cached

    @property
    def user_free(self):
        """This is the free memory available for the user"""
        return self._convert * (self._free + self._buff + self._cached)

    @property
    def swap(self):
        return self._convert * self._swapt

    @property
    def swap_free(self):
        return self._convert * self._swapf

    @property
    def swap_used(self):
        return self._convert * self._swapu


def show_lines_for_headless(lines):
    """
    Show lines on tty1. This writes text lines to picoLCD screens if the
    server has no video card (tested on Debian 10 netinstall with no
    special picoLCD-related packages).
    """
    # See <https://stackoverflow.com/questions/20894969/
    # python-reading-and-writing-to-tty>
    # (uses mode os.RDRW)
    tty = os.open("/dev/tty1", os.O_WRONLY)
    count = 0
    if lines is not None:
        for line in lines:
            if count < _MAX_LINES:
                if line is not None:
                    os.write(tty, str.encode("\n" + line))
                else:
                    os.write(tty, b"\n")
                count += 1
    for i in range(_MAX_LINES - count):
        os.write(tty, b"\n")
    os.close(tty)


def show_lines(lines):
    # TODO: This is not tested. Use run from from pypicolcd.command_line
    # directly instead.
    results = {"error": "contacting the server did not complete"}
    # See <https://www.saltycrane.com/blog/2008/09/
    # how-get-stdout-and-stderr-using-python-subprocess-module/>
    args = ['lcd-cli']
    args.extend(lines)
    wgproc = subprocess.Popen(args, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
    (standardout, junk) = wgproc.communicate()
    results = json.loads(standardout)
    return results


k_div = 1024
m_div = k_div * 1024
g_giv = m_div * 1024


def freeSpaceAt(path, unit="bytes", places=2):
    """
    Get the current free space on the drive that contains a specific
    path.

    Sequential arguments:
    path -- a path under a drive, or the exact path of a drive.

    Keyword arguments:
    unit -- (default: "bytes") The unit to use: bytes, kb, mb, gb (or
        the respectively synonymous b, k, m, or g).
    places -- (default: 2) The maximum number of decimal places to
        return. It it always 0 if using bytes.

    Returns:
        Get a float (integer if bytes) representing free space.
    """
    # See Mechanical snail's Sep 8, 2012 answer (edited by Mark Amery
    # Apr 13, 2019)
    # on <https://stackoverflow.com/questions/4260116/
    # find-size-and-free-space-of-the-filesystem-containing-a-given-
    # file>
    statvfs = os.statvfs(path)
    # statvfs.f_frsize * statvfs.f_blocks     # Size in bytes
    # statvfs.f_frsize * statvfs.f_bfree      # Actual free bytes
    # statvfs.f_frsize * statvfs.f_bavail     # free bytes for users
    #                                           (excl. reserved space)
    try:
        bfree = long(statvfs.f_bfree) * long(statvfs.f_bsize)
    except NameError:
        # Python 3 is always long
        bfree = statvfs.f_bfree * statvfs.f_bsize
    ret = None
    # fmt = "0:." + str(places) + "f"
    if (unit.lower() == "bytes") or (unit.lower() == "b"):
        ret = bfree
    elif (unit.lower() == "kb") or (unit.lower() == "k"):
        ret = round(bfree/k_div, places)
    elif (unit.lower() == "mb") or (unit.lower() == "m"):
        ret = round(bfree/m_div, places)
    elif (unit.lower() == "gb") or (unit.lower() == "g"):
        ret = round(bfree/g_div, places)
    return ret


def freeSpaceAtFmt(path, unit="bytes", places=2):
    fmt = "{:." + str(places) + "f}"
    if unit == "bytes":
        fmt = "{:.0f}"
    n = freeSpaceAt(path, unit=unit)
    return fmt.format(n)


def generate_action(action, lines, x=None, y=None):
    action = copy.deepcopy(action)
    if x is not None:
        action["x"] = int(x)
    if y is not None:
        action["y"] = int(y)
    action["lines"] = lines
    return action


def main():
    # show_lines_for_headless(["Hello World!"])
    slash_name = "primary /"
    drive2_name = "Home"
    stat_order = ["Memory", drive2_name, slash_name]
    stats = {}

    f = FreeMemLinux()
    # print(f.total, f.used,  f.user_free)
    # f_mb = FreeMemLinux(unit='MB')
    # f_percent = FreeMemLinux(unit='%')
    paths = {}
    paths[drive2_name] = os.environ.get("HOME")
    if paths[drive2_name] is None:
        paths[drive2_name] = os.environ.get("USERPROFILE")
    # freemem = FreeMemLinux(unit='%')
    unit = 'mb'
    freemem = FreeMemLinux(unit=unit)
    stats["Memory"] = "{:.2f} {}".format(
        freemem.total - freemem.used,
        unit
    )

    if platform.system() == "Windows":
        paths[slash_name] = "C:\\"
        del paths[drive2_name]
        stat_order.remove(drive2_name)
        if os.path.isdir("D:\\"):
            drive2_name = "D:"
            paths[drive2_name] = "D:\\"
            stat_order.append(drive2_name)
        else:
            drive2_name = None

    if drive2_name is not None:
        if paths[drive2_name] is not None:
            stats[drive2_name] = "{} {}".format(
                freeSpaceAtFmt(paths[drive2_name], unit=unit),
                unit
            )
        else:
            stats[drive2_name] = "?"
    paths[slash_name] = "/"
    stats[slash_name] = "{} {}".format(
        freeSpaceAtFmt(paths[slash_name], unit=unit),
        unit
    )
    if drive2_name is not None:
        if stats[slash_name] == stats[drive2_name]:
            del stats[drive2_name]
            stat_order.remove(drive2_name)
    pfsm = 1.5  # proportionally-spaced font space multiplier
    stat_list = []
    name_max = 0
    stat_max = 0
    for name in stat_order:
        if len(name) > name_max:
            name_max = len(name)
        if len(stats[name]) > stat_max:
            stat_max = len(stats[name])
    if stat_max < 13:
        stat_max = 13
        # such as "1000000.00 mb"
        # (which is1 tb)

    name_max = int(round(float(name_max) * pfsm))
    fmt = "{:<" + str(name_max) + "} {:>" + str(stat_max) + "}"
    for name in stat_order:
        if name in stats.keys():
            stat_list.append(
                fmt.format(name + ":", stats[name])
            )
        else:
            stat_list.append(fmt.format(name, "missing"))
    args = [sys.argv[0]]
    params = {}

    # Parse the params for filtering only
    # --still pass them as terminal params.
    custom_lines = []
    custom_params = {}
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if arg.startswith("--") and not arg.startswith("---"):
            ender = len(arg)
            sign_i = arg.find("=")
            value = True
            if sign_i > -1:
                ender = sign_i
                value = arg[sign_i+1:]
            name = arg[2:ender]
            if name == "headless":
                # TODO: implement this local command on the server
                params[name] = True
            elif name in get_commands():
                params[name] = True
            elif name in get_bool_options():
                params[name] = to_bool(value)
            else:
                params[name] = value
            print("* {}={}".format(name, value))
        else:
            custom_lines.append(arg)
    x = params.get("x")
    y = params.get("y")
    clock_d = None
    batches = {}
    order = ["timestamp", "stats"]
    if params.get("clock") is not None:
        # Generate clock BEFORE x and y are set forcibly below.
        clock_d = generate_action(params, None)
        batches["clock"] = clock_d
        del params["clock"]  # don't keep putting clock everywhere below
        order.append("clock")
    if x is None:
        x = 0
    if y is None:
        y = 0
    top = 39
    stat_d = generate_action(params, stat_list, x=0, y=top)

    now = datetime.now()
    now_s = now.strftime("%Y-%m-%d %H:%M:%S")
    # args[len(args)-1] += "\t\t{}".format(now_s)

    batches["stats"] = stat_d
    timestamp_lines = []
    timestamp_lines.append("on {}".format(os.uname()[1]))
    timestamp_lines.append("@" + now_s)
    # x=153 puts rightmost pixel of "@____-%m-%d %H:%M:%S" at the edge
    push_down = (len(stat_list)-len(timestamp_lines))*8
    timestamp_d = generate_action(params, timestamp_lines, x=153,
                                  y=top+push_down)
    batches["timestamp"] = timestamp_d

    if len(custom_lines) > 0:
        # for k, v in params.items():
        #     if (k != "clear") and (k != "y"):
        #         print("* more lines: --{}={}".format(k, v))
        #         custom_lines.append("--{}={}".format(k, v))
        custom_d = generate_action(params, custom_lines, x=y, y=y)
        batches["custom"] = custom_d
        order.append("custom")
        # print("{} custom line(s)".format(len(custom_lines)))
    else:
        print("There are no custom lines.")
    first = True
    for key in order:
        print("")
        action = batches[key]
        if not first:
            try:
                del action["clear"]
            except KeyError:
                pass
        first = False
        results = lcdclient.send_action(action)
        if results.get("status") != "OK":
            print('* {}'.format(results))
            print("  * in response to showing {}:"
                  " '{}'".format(key, action))
            if action.get('headless') is True:
                print("* attempting to write to tty1 (which could be a"
                      " picoLCD display on a headless server)...")
                if "lines" in action:
                    show_lines_for_headless(action["lines"])
        else:
            # print("  * in response to '{}'".format(action))
            info_s = results.get("info")
            if info_s is not None:
                del results["info"]
            print('* {}'.format(results))
            if info_s is not None:
                print("\n".join(info_s.split("\\n")))


if __name__ == "__main__":
    main()
