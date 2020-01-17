 # Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).


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
- (fix use of refresh_enable) make force_refresh_enable=True work where on=False
