# pypicolcd
<https://github.com/expertmm/pypicolcd>
Draw to picoLCD 256x64 and 20x4 using only pyusb (no driver required!) by importing the PicoLcd class.

## Main Features
* Draw without driver
* Fast: refresh only refreshes zones invalidated--even faster if you do `picolcd.set_pixel(x, y, True, refresh_enable=False)` then call `picolcd.refresh()` after all `set_pixel` calls are done (`draw_text` does this automatically)
* Draw without dependencies other than pyusb (`sudo python3 -m pip install pyusb`) and PIL (`sudo python3 -m pip install Pillow` or `sudo python -m pip install Pillow` or on arch, `pacman -Syu python-pillow`)
* Fault-tolerant: draw text or image beyond range of screen, and automatically gets cropped (negative pos is allowed, which can be used for sprite animations if 64x64 cells in column or 256x64 cells in any layout)

## Planned Features
* more accurate image dithering

## Changes
(2018-01-26)
* make example.py
* (fix use of refresh_enable) make force_refresh_enable=True work where on=False
* draw text
* draw image with font or dithering

## Developer Notes

### What is testing.py
* Sends random bytes to your picoLCD without a driver!
* Draw a pixel by clicking on the canvas.

### Communication Protocol
(only picoLCD 256x64 was tested)
You must sent a byte array. Python will throw an exception if any integer in `this_list` is >255. `bytes(this_list)`.
In LANDSCAPE orientation:
* The term "block" here is used to refer to a 8x32 pixel area (made up of 32 bytes on the 1-bit screen buffer)
* Each byte on the chip holds 8 VERTICAL pixels
* There are 4 chips from left to right--each chip has 2 zones,
  so there are 8 zones from left to right
* There are 8 blocks (8 rows of blocks) from top to bottom (the official driver calls this a "line" which is misleading since it is an irreducible 8 pixels tall)
* long command:
  * has 11 bytes plus a length byte and data bytes
  * purpose is to select and write block and zone (but cannot select odd zones and cannot change x pixel location except in relative positioning which is not usually used with long command)
  * absolute positioning when `[8]` is 0x40 (always use 0x40 for long command)
* short command:
  * has 4 bytes plus a length byte and data bytes
  * only short command can access a block in an odd zone (right side) of a chip
  * long command must select block and chip before short command is called
  * normally, long command writes 32 bytes (0x20), then if right side of chip needs to be accessed, short command is also called
    * writes next 32 bytes (short command must be called immediately after long command writes byte 31, due to relative positioning being the only way to access the right side of the chip aka odd zone)
    * therefore, accessing a block in an odd zone always requires first filling the even zone (for example, filling zone 1 block 3 requires filling zone 0 block 3 using long command with 32 bytes then calling short command to fill zone 1 block 3, where zone 1 and block 3 are implied by relative positioning, also with 32 bytes)
* pypicolcd stores blocks separately so they can be sent to the graphics chip without slicing the list


## Authors
* resources from external sources:
  * Ninepin font: by Digital Graphics Labs on <http://www.1001fonts.com/ninepin-font.html> LICENSE is "fonts/1001Fonts General Font Usage Terms.txt" except with the following specifics stated by author: Free for personal use, Free for commercial use, Modification NOT allowed, Redistribution allowed, freeware license in "fonts/ninepin/!license.txt"
  * Press Start font family (prstart.ttf, prstartk.ttf): by codeman38 on <http://www.1001fonts.com/press-start-font.html> LICENSE is "fonts/1001Fonts General Font Usage Terms.txt" except with the following specifics stated by author: Free for personal use, Free for commercial use, Modification allowed, Redistribution allowed, custom license "fonts/press-start/license.txt"
    * naturally 8px high including descenders
  * flottflott font: by Peter Wiegel on <http://www.1001fonts.com/flottflott-font.html>  LICENSE is "fonts/1001Fonts General Font Usage Terms.txt" except with the following specifics stated by author: Free for personal use, Free for commercial use, Modification allowed, Redistribution allowed, SIL Open Font License (OFL) -- see "fonts/flottflott/Open Font License.txt" and "fonts/flottflott/OFL-FAQ.txt"
* expertmm <https://github.com/expertmm> code and resources not mentioned above: resources created by expertmm are CC0 -- see "images/CC0.txt")
* sphinx on excamera.com: http://excamera.com/sphinx/article-picolcd.html (61-line version of code that works with text model picoLCD 20x4 only)
