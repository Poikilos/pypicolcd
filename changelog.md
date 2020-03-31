# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.0.0/).


## [git] - 2020-03-31
### Fixed
- (lcd-cli) Respond to `--help` or no params with usage.
- Fix the level 1 Markdown heading in the Changelog.

### Changed
- Make the usage text accessible via static methods.
- If `ConnectionRefusedError` occurs, suggest using `--host=<lan_ip>`
  instead of default (localhost).


## [git] - 2020-01-23
### Added
- KeepAlive thread for recovering clock and reconnecting in that case.
- Add `refresh` command (calls `invalidate()` and `refresh()`).

### Changed
- Avoid resetting the framebuffer on reconnect.
- Recover clock thread on reconnect.
- Use clock thread to discover that a disconnect occurred (to force
  refresh from buffer in that case).


## [git] - 2020-01-23
### Changed
- Rename "brightness" option to "backlight" to make room for future
  brightness option which could apply to the image brightness
  (pre-dithering multiplier).
- Move lcdclient to a separate module, and simplify stats.py by using
  lcdclient instead of command_line.
- Finish the clock option (separate x and y params for clock from
  others).


## [git] - 2020-01-23
### Added
- Allow custom text along with the lcd-stats command.

### Changed
- Improve input and output.
- (install-lcd-fb.sh) Fix service file generation.
- Fix Python 2 compatibility.
- Fix lcd-stats argument processing.
- Fix handle_error
- Fix handle_signal (close the server when OS sends a signal).
- Improve quality.sh and make PEP8 changes.
- Fix use of clear, x, and y with the lcd-stats command.
- Improve documentation including docstrings.
- Make stats have a fixed width to ensure they overwrite previous
  values.


## [git] - 2020-01-21
### Added
- Create a server so that the buffer remains the same for multiple
  programs and `lcd-cli` calls.
- Set the following new params using lcd-cli (or by sending JSON to the
  http framebuffer server directly, or by utilizing the PicoLCD
  push_action method some other way):
  - `font`
  - `x`
  - `y`
- Install as service on GNU+Linux systems using the new
  "install-lcd-fb.sh" script.

### Changed
- Clean up Draw objects for fonts (resolves issue #1 core dump in
  `draw_text` presumably).
  - This may introduce some latency, but only the first time a
    character is used during the entire run of the framebuffer server.
- `draw_lines` now accepts pixel locations as a top left corner.
- The `push_text` method (such as utilized via the `push` option) now
  acts upon `\t`, `\n`, and `\r` control characters (escaped or
  literal).
- Calculate the width of the space character (as `space_w`)
  automatically in push_text (formerly it used `3` literally).
- rename lcd-daemon to lcd-fb


## [git] - 2020-01-20
### Added
- Create a framebuffer server with a persistent connection.


## [git] - 2020-01-19
### Added
- Add a udev rules file that matches the one the program generates for a
  picoLCD 256x64 Sideshow.

### Changed
- Improve udev rule instructions
  - ATTRS, which checks parent devices, also works. ATTR does not check
    parent devices, but still works.
    - See
      <https://github.com/JamesTheAwesomeDude/pyPicoLCD/blob/full-reimplimentation/60-lcd.rules>
- Handle disconnects (see readme.md).
- Fix backlight level method (and rename to `set_backlight`).
- Fix flash method.
- Allow sending bytestrings of arbitrary length using testing.pyw.


## [git] - 2020-01-17
### Added
- The pip install now includes the necessary data files (fonts and
  images) via the added MANIFEST.in for setuptools.

### Changed
- The command is now lcd-cli (It still uses command_line.py).
- The pip install now works properly, and imports work properly.
- The module name is now consistent (pypicolcd).
- Old changes from the readme.md are now in this file.


## [git] - 2020-01-15
### Added
- There is now a pypicolcd-cli command (that uses command_line.py).
- Create a Changelog.

### Changed
- Refactor the project to make it into a setuptools package.
  - Adjust install instructions to match (easier and using virtualenv).
- Change case of classes from PicoLcd to PicoLCD


## [git] - 2018-01-26
### Added
- make example.py [later renamed to example-cli.ty]
- draw text
- draw image with threshold OR dithering

### Changed
- (fix use of refresh_enable) make force_refresh_enable=True work where
  on=False
