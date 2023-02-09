# -*- coding: utf-8 -*-
'''
If 0 devices are listed and you are using Windows, see Windows section
of readme.
'''
# <https://www.orangecoat.com/how-to/use-pyusb-to-find-vendor-and-product-
#   ids-for-usb-devices>


import sys
import usb.core
# find USB devices
dev = usb.core.find(find_all=True)
# loop through devices, printing vendor and product ids in decimal and hex
count = 0
for cfg in dev:
    count += 1
    sys.stdout.write('Decimal VendorID=' + str(cfg.idVendor) + ' & ProductID=' + str(cfg.idProduct) + '\n')
    sys.stdout.write('Hexadecimal VendorID=' + hex(cfg.idVendor) + ' & ProductID=' + hex(cfg.idProduct) + '\n\n')
print("Found {}".format(count))
if count == 0:
    print(__doc__)
