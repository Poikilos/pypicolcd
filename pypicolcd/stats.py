#!/usr/bin/env python3
from pypicolcd.command_line import run

import os
import sys
import platform
from datetime import datetime

_MAX_LINES = 4

# See [Oz123's answer](https://stackoverflow.com/a/24186720)
# Jun 12, 2014 (edited Oct 7, 2016; accessed Jan 14, 2020)
# on https://stackoverflow.com/questions/17718449/determine-free-ram-in-python
class FreeMemLinux(object):
    """
    Non-cross platform way to get free memory on Linux. Note that this code
    uses the `with ... as`, which is conditionally Python 2.5 compatible!
    If for some reason you still have Python 2.5 on your system add in the
head of your code, before all imports:
    from __future__ import with_statement
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
        return self._convert *(self._free + self._buff + self._cached)

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
    # See https://stackoverflow.com/questions/20894969/python-reading-and-writing-to-tty
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
    results = {"error": "contacting the server did not complete"}
    # See <https://www.saltycrane.com/blog/2008/09/
    # how-get-stdout-and-stderr-using-python-subprocess-module/>
    wgproc = subprocess.Popen(['wget', '-r', '--tries=10', 'http://fly.srk.fer.hr/', '-o', 'log'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (standardout, junk) = wgproc.communicate()
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
    # See Mechanical snail's Sep 8, 2012 answer (edited by Mark Amery Apr 13, 2019)
    # on https://stackoverflow.com/questions/4260116/find-size-and-free-space-of-the-filesystem-containing-a-given-file
    statvfs = os.statvfs(path)
    # statvfs.f_frsize * statvfs.f_blocks     # Size of filesystem in bytes
    # statvfs.f_frsize * statvfs.f_bfree      # Actual number of free bytes
    # statvfs.f_frsize * statvfs.f_bavail     # Number of free bytes that ordinary users
                                              # are allowed to use (excl. reserved space)
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

def main():
    # show_lines_for_headless(["Hello World!"])
    stat_order = ["Memory", "Home", "root"]
    stats = {}

    f = FreeMemLinux()
    # print(f.total, f.used,  f.user_free)
    # f_mb = FreeMemLinux(unit='MB')
    # f_percent = FreeMemLinux(unit='%')
    paths = {}
    paths["Home"] = os.environ.get("HOME")
    if paths["Home"] is None:
        paths["Home"] = os.environ.get("USERPROFILE")
    # freemem = FreeMemLinux(unit='%')
    unit = 'mb'
    freemem = FreeMemLinux(unit=unit)
    stats["Memory"] = "{:.2f} {}".format(freemem.total - freemem.used, unit)
    # Assumes home is sdb1:
    if paths["Home"] is not None:
        stats["Home"] = "{} {}".format(freeSpaceAtFmt(paths["Home"], unit=unit), unit)
    else:
        stats["Home"] = "?"
    paths["root"] = "/"
    if platform.system() == "Windows":
        paths["root"] = "C:\\"
    stats["root"] = "{} {}".format(freeSpaceAtFmt(paths["root"], unit=unit), unit)

    stat_list = []
    for name in stat_order:
        if name in stats.keys():
            stat_list.append("{}: {}".format(name, stats[name]))
        else:
            stat_list.append("{}: missing".format(name))
    args = sys.argv
    params = {}

    # Parse the params for filtering only
    # --still pass them as terminal params.
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if arg.startswith("--") and not arg.startswith("---"):
            ender = len(arg)
            sign_i = arg.find("=")
            value = True
            if sign_i > -1:
                ender = sign_i
                value = arg[sign_i+1:]
            name = arg[2:sign_i]
            params[name] = value
    y = params.get("y")
    if y is None:
        y = 39
    else:
        y = int(y)
    if "y" not in params:
        args.append("--y={}".format(y))

    args.extend(stat_list)
    now = datetime.now()
    now_s = now.strftime("%Y-%m-%d %H:%M:%S")
    # args[len(args)-1] += "\t\t{}".format(now_s)
    batches = []
    batches.append(args)
    time_args = [sys.argv[0]]
    time_args.append("@" + now_s)
    time_args.append("--x=128")
    time_args.append("--y={}".format(y+16))
    for k, v in params.items():
        time_args.append("--{}={}".format(k, v))
    batches.append(time_args)
    for current_args in batches:
        results = run(current_args)
        if results.get("info") != "OK":
            print('* {}'.format(results))
            if "--headless" in sys.argv:
                print("* attempting to write to tty1 (which could be a picoLCD"
                      " display on a headless server)...")
                show_lines_for_headless(stat_list)
        else:
            print('* {}'.format(results))


if __name__ == "__main__":
    main()