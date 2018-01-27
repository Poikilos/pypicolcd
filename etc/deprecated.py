# region formerly from pypycolcd.py
try:
    import Tkinter as tk
    import tkFont
    import ttk
except ImportError:  # Python 3
    import tkinter as tk
    import tkinter.font as tkFont
    import tkinter.ttk as ttk

class PicoLcd_DEPRECATED:
    # enable: True is black, as False allows backlight to show through
    # this is very inaccurate, and not changed to match info in README yet
    def _pokepixel(self, x, y, enable, diff_enable=True):
        addr = None
        print("[ picolcd ] ERROR in _pokepixel: Nothing done since"
              " seems impossible (don't ever use _pokepixel)")
        return 0
        if self.dc["type"] == "text":
            print("[ picolcd ] ERROR in _pokepixel: not available in"
                  " text device type")
            return 0
        # see patched lcd4linux source on
        # http://www.linuxconsulting.ro/picoLCD/
        # * goto/write command is
        #   [0x98, y, x, len, rawdata]
        # 128, 192, 148, 212
        # addr = {0: 0x80, 1: 0xc0, 2:0x94, 3:0xd4}[y] + x
        data_len = 1
        data = 1 << (x%self.dc["ppb"])
        byte_x = int(x/self.dc["ppb"])  # since 1-bit graphics
        pitch = int(self.dc["width"] / self.dc["ppb"])
        byte_i = y * pitch + byte_x
        # NOTE: official driver uses whole byte of framebuffer as bool
        # but this code keeps actual copy of byte, where only bits are
        # on where the pixel is on as per the destination (1-bit) format
        dest_data = self.framebuffer[byte_i]
        cs = int(byte_i/self.dc["chip_size"])

        chipsel = cs << 2
        # chipsel | 0x01 clears bottom (landscape right) of chip
        # (only seems to work with relative positioning)
        # self.wr(bytes(OUT_REPORT_DATA, y, x, data_len, data))
        # if line is None:
        # line = int(x/8)
        chip_height_px = int(
            (self.dc["chip_size"] * self.dc["ppb"])
            / self.dc["width"]
        )
        local_y = y - (cs * chip_height_px)
        sidestep = int(x/self.dc["ppb"])
        halfchip_height = int(chip_height_px/2)
        chipside = int(round(y/halfchip_height))
        # for [5] there are 8 lines, so line b8|line could be:
        # |0, |1, |2, |3, |4, |5, |6, |7
        # b8, b9, ba, bb, bc, bd, be, bf
        # starting from top down in landscape view

        # chipsel (at [1]) is cs << 2 where cs is chip number 0-3
        # (in the short command it is |1)
        # 00, 04, 08, 0c (for long command)
        # |1, |1, |1, |1
        # 01, 05, 09, 0d (for short command)
        cmd3 = [
            OUT_REPORT_CMD_DATA,
            byte_i, # chipsel | chipside,  # this is a BYTE
            0x02,
            0x00,
            0x00,
            0x00, # [5] sidestep,  # 0xb8|sidestep,  # 0xb8|line,
            0x00,
            0x00,
            0x00,# 0x40,
            0x00,
            0x00,
            data_len
        ]

        cmd4 = [
            OUT_REPORT_DATA,
            chipsel | chipside,
            0x00,
            0x00,
            data_len
        ]
        cmd4_data_start = len(cmd4)
        # for index in range(data_len):
        if (not diff_enable) or ((data | dest_data) != dest_data):
            # result_data = data
            # if diff_enable:
            result_data = data
            # NOTE: official driver's frame buffer has OxFF
            # if pLG_framebuffer[y * 256 + x] ^ self.dc["inverted"]:
                # pixel |= (1 << bit);
            # representing one bit (eight times bigger than chip_size)
            # if self.framebuffer[byte_i) ^ self.dc["inverted"] > 0:
                # if differs from framebuffer
            result_data |= self.framebuffer[byte_i]
            self.framebuffer[byte_i] = result_data

            cmd3.append(result_data)
            cmd4.append(result_data)
            # self.wr(cmd3)
            self.wr(cmd4)

    def clear(self, val=0x00, data_len=32, line_len=8, chip_count=4):
        # self.framebuffer = [0] * (self.dc["width"] * self.dc["height"])
        self.reset_framebuffer()
        if self.dc["type"] == "text":
            for row in range(self.dc["height"]):  # formerly range(4)
                self.draw_text(row, 0, " " * self.dc["width"])  # formerly * 20
        else:  # self.dc["type"] == "graphics":
            addr_count = 0
            # print("[ picocld ] clearing pixels 2nd slowest way...")
            # for row in range(self.dc["height"]):
            # formerly range(4)
                # self.setpixel(row, 0, " " * self.dc["width"])
                # formerly * 20
            # see patched lcd4linux source at
            # http://www.linuxconsulting.ro/picoLCD/
            for cs in range(chip_count):
                chipsel = cs << 2
                for line in range(line_len):
                    # data = []
                    cmd3 = [
                        OUT_REPORT_CMD_DATA,
                        chipsel,
                        0x02,
                        0x00,
                        0x00,
                        0xb8|line,
                        0x00,
                        0x00,
                        0x40,
                        0x00,
                        0x00,
                        data_len
                    ]
                    cmd3_data_start = len(cmd3)
                    cmd4 = [
                        OUT_REPORT_DATA,
                        chipsel | 0x01,
                        0x00,
                        0x00,
                        data_len
                    ]
                    cmd4_data_start = len(cmd4)
                    for index in range(data_len):
                        # data.append(0x00)
                        # extend list for now--set to pixel later
                        cmd3.append(0x00)
                        cmd4.append(0x00)
                    SCREEN_H = self.dc["height"]
                    SCREEN_W = self.dc["width"]
                    # each cs handles 1 64x64 pixel memory chip
                    # each index paints 2 rows
                    # (memory is addressed from landscape perspective)
                    for index in range(data_len):
                        pixel = val
                        offset = cmd3_data_start + index

                        for bit in range(8):
                            x = cs * 64 + index;
                            y = (line * 8 + bit + 0) % SCREEN_H
                            # TODO (from official driver but seems
                            # wrong since XOR does not change left
                            # param bit if right param bit is zero):
                            # if self.framebuffer[y * 256 + x] ^ \
                                    # self.dc["inverted"] > 0:
                            pixel |= (1 << bit)
                        if val == 0x00:
                            cmd3[offset] = 0x00
                        else:
                            cmd3[offset] = pixel
                    for i in range(data_len):
                        index = i + 32
                        pixel = val
                        for bit in range(8):
                            x = cs * 64 + index;
                            y = (line * 8 + bit + 0) % SCREEN_H
                            # TODO (from official driver but seems
                            # wrong since XOR does not change left
                            # param bit if right param bit is zero):
                            # if self.framebuffer[y * 256 + x] ^ self.dc["inverted"]:
                            pixel |= (1 << bit)

                        if val == 0x00:
                            cmd4[cmd4_data_start + (index - 32)] = 0x00
                        else:
                            cmd4[cmd4_data_start + (index - 32)] = pixel
                        addr_count += 1
                    # clear top (landscape left) of this chip:
                    self.wr(cmd3)
                    # clear clear bottom (landscape right) of this chip:
                    self.wr(cmd4)
                # end for line
            # end for cs (chip index)
            print("[ picolcd ] cleared " + str(addr_count)
                  + " block(s)")
            pass

    # row,col: the y,x location (in that order; though if
    # picolcd.dc["type"] is graphics, it will be a pixel location
    # where row is the middle of the letters)
    def draw_text(self, row, col, text, font=None):
        if self.dc["type"] == "graphics":
            start_y = row
            start_x = col

            # print("[ picolcd ] ERROR in draw_text:"
                  # " bitmap font, required for draw_text in "
                  # " graphics model type, is not yet implemented")
            root0 = tk.Tk()  # never shown, just for font rendering
            canvas = tk.Canvas(root0, width=self.dc["width"],
                               height=self.dc["height"])
            canvas.pack()
            bg_id = canvas.create_rectangle(0, 0, self.dc["width"],
                                            self.dc["height"],
                                            fill="WHITE")
            text_id = None
            black_count = 0
            unknowns = []
            if font is not None:
                text_id = canvas.create_text(
                    start_x, start_y, anchor=tk.W,
                    fill="BLACK", # fill="#000"
                    text=text,
                    font=font)
            else:
                text_id = canvas.create_text(
                    start_x, start_y, anchor=tk.W,
                    fill="BLACK",
                    text=text)
            on_count = 0
            # pixels = get_pixels_1d_of(canvas)
            # for p_i in range(len(pixels)):
                # pixel = pixels[p_i]
                # if pixel == "BLACK":
                    # y = int(p_i / self.dc["width"])
                    # x = int(p_i % self.dc["width"])
                    # self.set_pixel(x, y, True, refresh_enable=False)
                # elif pixel == "WHITE":
                    # pass
                # else:
                    # if pixel not in unknowns:
                        # unknowns.append(pixel)
            rows = get_pixels_2d_of(canvas)
            y = 0
            for row in rows:
                x = 0
                for pixel in row:
                    if pixel == "BLACK":
                        on_count += 1
                        self.set_pixel(x, y, True, refresh_enable=False)
                    elif pixel == "WHITE":
                        pass
                    else:
                        if pixel not in unknowns:
                            unknowns.append(pixel)
                    x += 1
                y += 1

            if len(unknowns) > 0:
                print("[ PicoLcd ] WARNING in draw_text: offscreen"
                      " surface had unknown pixels: "
                      + str(unknowns))

# endregion formerly from pypycolcd.py
