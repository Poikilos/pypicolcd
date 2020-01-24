# pypicolcd
<https://github.com/poikilos/pypicolcd>


Draw to picoLCD 256x64 and 20x4 using only pyusb (no driver required!) by importing the PicoLCD class.
![kitten](https://github.com/poikilos/pypicolcd/raw/master/screenshot.jpg)

## Main Features
* Easy: see <https://github.com/poikilos/pypicolcd/blob/master/example.py>
* Draw without driver
* Fast: refresh only refreshes zones invalidated
* Draw without dependencies other than pyusb and PIL
* Fault-tolerant: draw anything beyond range of LCD and will not crash nor miss good parts
* Image Dithering: draw color image, and it will automatically be dithered to 1-bit by luminosity (threshold is also possible)
* Persistent Framebuffer: The lcd-fb script (which runs lcdframebuffer.py) runs a server. The lcd-cli script (which runs command_line.py) is the client.
  - By default, they only communicate with localhost. To use the server over the LAN:
    - On the client, specify `lcd-cli --host ...` where `...` is the server's IP address after doing the following steps:
    - On the server, ensure incoming traffic on port 25664 is allowed.
    - On the server, specify your IP address when running the server (change the service file if you run it as a service):
```bash
lcd-fb --localhost=`hostname -i`
```
where `\`hostname -i\`` is your IP address.

## Compare
- This module does not require a (non-Python kernel) driver unlike pyusblcd in the PyPI repository.
- This module has a persistent framebuffer server unlike other driverless modules named similarly such as [JamesTheAwesomeDude/pyPicoLCD](https://github.com/JamesTheAwesomeDude/pyPicoLCD) and [itszero/picoLCD256x64](https://github.com/itszero/picoLCD256x64).
- This module uses pyusb for driverless access and implements a lcd-cli command similarly to how [rebeccaskinner/lcddeamon](https://github.com/rebeccaskinner/lcddeamon) uses libusb for driverless access and implements a usblcd command, but that daemon is written in c.

## Install
- pypicolcd uses Python 3, and though has some Python 2 considerations, is not thoroughly tested on Python 2. Therefore, make sure virtualenv is Python 3 by default, otherwise follow a guide to use the Python 3 virtualenv (such as [Installing and using virtualenv with Python 3](https://help.dreamhost.com/hc/en-us/articles/115000695551-Installing-and-using-virtualenv-with-Python-3)).
- Install via pip to get all dependencies:
```bash
customDie() {
    echo
    echo
    echo "ERROR:"
    echo "$1"
    echo
    echo
    exit 1
}
cd ~
# if [ ! -d "lcd" ]; then
#     mkdir lcd || customDie "'mkdir lcd' failed in `pwd` as $USER"
# fi
# cd lcd || customDie "'cd lcd' failed in `pwd`."
if [ -d "lcd" ]; then
    customDie "`pwd`/lcd already exists. Try removing it, or run the remaining commands (after and not including 'virtualenv lcd') if it is already a virtualenv"
fi
virtualenv lcd || customDie "'virtualenv lcd' failed in `pwd` as $USER"
source lcd/bin/activate || customDie "'source lcd/bin/activate' failed in `pwd`"
pip install pip --upgrade || customDie "'pip install pip --upgrade' failed in `pwd` as $USER"
option=""
if [ ! -z "`pip list | grep -F pypicolcd`" ]; then
    option="--upgrade"
fi
pip install $option https://github.com/poikilos/pypicolcd/archive/master.zip || customDie "'pip install octoprint --upgrade' failed in `pwd` as $USER"
deactivate


```
- The pip install automatically gets the dependencies:
  - pyusb (formerly `sudo python3 -m pip install pyusb`)
  - PIL (formerly `sudo python3 -m pip install Pillow` or `sudo python -m pip install Pillow` or on arch, `pacman -Syu python-pillow`)

- Then you must run lcd-fb on startup. For linux, you can do the
  following:
  - `cd ~ && git clone https://github.com/poikilos/pypicolcd.git`
  - `cd pypicolcd`
  - `./install-lcd-fb.sh`
  - edit the following script if your LAN is something other
    than 192.168.1.*:
  - `"./allow port 25664 only from 192.168.1 network.sh"`
- You must also allow the unpriveleged user to send data on the USB port
  if the server prompts you with instructions on how to do that. Run
  example-cli.py or testing.pyw to view the instructions for linux.

### Update The Server
(The pip command below also updates the client.)
- First, activate the virtualenv if present such as by running `~/lcd/bin/activate`, then:
  `pip install --upgrade https://github.com/poikilos/pypicolcd/archive/master.zip && rm -rf ~/lcd/lib/python3.7/site-packages/pypicolcd/__pycache__/ && sudo systemctl daemon-reload && sudo systemctl restart lcd-fb`
- Or, if you have a local copy of the git repo:
  - You still must activate the venv, such as by running `~/lcd/bin/activate`, then do
  `pip install --upgrade ~/git/pypicolcd && rm -rf ~/lcd/lib/python3.7/site-packages/pypicolcd/__pycache__/ && sudo systemctl daemon-reload && sudo systemctl restart lcd-fb`

## Usage
* Draw Image:
  * pos is an x,y tuple
  * negative pos is allowed, which can be used for sprite animations if 64x64 cells in single-column layout or 256x64 cells in any layout
  * see comments above draw_image in picousb.py for more info
* Draw Text:
  * draw_text function's row, col format is y,x order (is considered 6x8 pixel blocks if `picolcd.dc["type"] == "graphics"`), but you can do draw_text_at to avoid that and use pixel locations directly (for text mode, these locations will be interpreted into col,row format in that order for draw_text_at function)
  * see comments above draw_text in picousb.py for more info
* Pixel manipulation:
  * For drawing many pixels at once, make your drawing faster by using `refresh_enable=False` (such as `picolcd.set_pixel(x, y, True, refresh_enable=False)`), then call `picolcd.refresh()` after all of your `set_pixel` calls are done (draw_text is an example of how to use this optimization)
  * get_pixel only works for pixels created during the life of the PicoLCD object, since it gets pixels from the offscreen pixelbuffers


## Known Issues
- [ ] If possible, read the state of buttons on the unit (also via pyusb).
- [ ] Add an option to disconnect from the device so it can be used by other processes.

## Troubleshooting
- Detecting resets (normally from the device being disconnected) is
  only possible if you try to write while the device is disconnected.
  Otherwise, the framebuffer (and canvas in testing.pyw) will remain
  incorrect until you call `clear()` on the PicoLCD instance (certain
  pixels involved in the command will not change if they would match the
  existing framebuffer--this is the expected behavior).

## Authors
* resources from external sources:
  * Ninepin font: by Digital Graphics Labs on <http://www.1001fonts.com/ninepin-font.html> LICENSE is "fonts/1001Fonts General Font Usage Terms.txt" except with the following specifics stated by author: Free for personal use, Free for commercial use, Modification NOT allowed, Redistribution allowed, freeware license in "fonts/ninepin/!license.txt"
  * Press Start font family (prstart.ttf, prstartk.ttf): by codeman38 on <http://www.1001fonts.com/press-start-font.html> LICENSE is "fonts/1001Fonts General Font Usage Terms.txt" except with the following specifics stated by author: Free for personal use, Free for commercial use, Modification allowed, Redistribution allowed, custom license "fonts/press-start/license.txt"
    * naturally 8px high including descenders
  * flottflott font: by Peter Wiegel on <http://www.1001fonts.com/flottflott-font.html>  LICENSE is "fonts/1001Fonts General Font Usage Terms.txt" except with the following specifics stated by author: Free for personal use, Free for commercial use, Modification allowed, Redistribution allowed, SIL Open Font License (OFL) -- see "fonts/flottflott/Open Font License.txt" and "fonts/flottflott/OFL-FAQ.txt"
  * zephyrean font family (zephyrea.ttf, zephyreg.ttf) by Ænigma Fonts on <http://www.1001fonts.com/zephyrean-font.html> LICENSE is "fonts/1001Fonts General Font Usage Terms.txt" except with the following specifics stated by author: Free for personal use, Free for commercial use, Modification NOT allowed, Redistribution allowed, custom "use them any way you want" license (see "fonts/zephyrean/zephyrean.txt")
  * ilyessuti on pixnio: CC0 licensed kitten*.jpg (2017-12-21-14-52-48) <https://pixnio.com/fauna-animals/cats-and-kittens/field-grass-cute-summer-nature-cat-outdoor-flower>, retouch poikilos -- see "images/CC0.txt"
* [poikilos](https://github.com/poikilos) code and resources not mentioned above: resources created by poikilos are CC0 -- see "images/CC0.txt")
* sphinx on excamera.com: http://excamera.com/sphinx/article-picolcd.html (61-line version of code that works with text model picoLCD 20x4 only)
  - Formerly, pypicolcd (before it was a module) required picolcd.py from http://excamera.com/sphinx/article-picolcd.html.


## Developer Notes
* Stripe caches (_s_cache) is a dict of dicts of list of bytes where each byte is a vertical stripe of 8 pixels (cached this way since device writes that way)
* To get font rect (for graphics type devices only), try something like
```python
last_rect = picolcd.draw_text(
    y, x, "|-------|",  # row,col format is in y,x order even though
                        # is pixel location if graphics type device
    erase_behind_enable=True, refresh_enable=False)
```
  then clear the LCD, or just store the numbers to a file or your code so the process doesn't need to be repeated on each run.
  Result will be a rect in format ((min_x, min_y), (max_x+1, max_y+1)) which can be later passed like `draw_text(y, x, "...", erase_rect=last_rect)`
* erase_behind_enable option will not erase beyond actual drawn rect (such as, overwriting "111" with "---" will still show the top and bottom of the 1s unless you pass erase_rect param (see above)
* contents of DC_DICT (and hence of picolcd.dc) should never be changed--they are device characteristics that define how the device operates at the lowest accessible level. If there is a different device not supported, the device should be added as a new entry in the DC_DICT, where the key is its USB device id.
* buffer state is not stored across runs, so clearing LCD should be done
  unless you only want to assign a certain slot to each program that
  displays things to it.

### What is testing.py
* Left Panel:
  * Draw Text or Draw Image (threshold will be used if Threshold is checked above the threshold value textbox)
    * If threshold unchecked, dithering will be used for Draw Image
* Right Panel:
  * Enable drawing a pixel by clicking on the canvas
  * Sends any bytes you want to your picoLCD without a driver!

### Communication Protocol
(only "picoLCD 256x64 Sideshow" was tested)

You must sent a byte array. Python will throw an exception if any integer in `this_list` is >255. `bytes(this_list)`.
In LANDSCAPE orientation:
* The term "block" here is used to refer to a 8x32 pixel area (made up of 32 bytes on the 1-bit screen buffer)
* Each byte on the chip holds 8 VERTICAL pixels
* There are 4 chips from left to right--each chip has 2 zones,
  so there are 8 zones from left to right
* There are 8 blocks (8 rows of blocks) from top to bottom (the official driver calls this a "line" which is misleading since it is an irreducible 8 pixels tall)
* long command:
  * has 11 bytes plus a length byte and data bytes
  * purpose is to select&write block&zone (but cannot select odd zones and cannot change x pixel location except in relative positioning which is not usually used with long command)
  * absolute positioning when `[8]` is 0x40 (always use 0x40 for long command)
* short command:
  * has 4 bytes plus a length byte and data bytes
  * only short command can access a block in an odd zone (right side) of a chip
  * long command must select block and chip before short command is called
  * normally, long command writes 32 bytes (0x20), then if right side of chip needs to be accessed, short command is also called
    * writes next 32 bytes (short command must be called immediately after long command writes byte 31, due to relative positioning being the only way to access the right side of the chip aka odd zone)
    * therefore, accessing a block in an odd zone always requires first filling the even zone (for example, filling zone 1 block 3 requires filling zone 0 block 3 using long command with 32 bytes then calling short command to fill zone 1 block 3, where zone 1 and block 3 are implied by relative positioning, also with 32 bytes)
* pypicolcd stores blocks separately (in picolcd.framebuffers list) so they can be sent to the graphics chip without slicing the buffer (only one framebuffer is created for text type devices)
