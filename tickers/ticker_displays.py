import random
import struct

import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageOps

from panda3d.core import Texture, TextureStage


class Ticker:

    def __init__(self, model, size, msg, **kwargs):
        self.model = model
        self.size = size

        self.display_settings(**kwargs)
        self.initialize(msg)

    def initialize(self, msg):
        self.tex = Texture('image')

        self.tex.setup_2d_texture(
            self.size.x,
            self.size.y,
            Texture.T_unsigned_byte,
            Texture.F_rgb
        )

        img = self.create_image(msg)
        self.tex.set_ram_image(img)
        self.model.set_texture(self.tex)
        self.mem_view = memoryview(self.tex.modify_ram_image())

    def update_image(self):
        self.tex.set_ram_image(self.mem_view)
        self.model.clear_color()
        self.model.set_texture(self.tex)

    def get_min_max_rows(self, img, color):
        idxes = np.where(np.all(img == color, axis=2))[0]
        return idxes[-1], idxes[0]


class SquareDisplay(Ticker):

    def __init__(self, model, size, msg):
        super().__init__(model, size, msg)

    def display_settings(self):
        self.font_face = cv2.FONT_HERSHEY_COMPLEX
        self.pixel_height = 80
        self.thickness = 6

        self.scale = cv2.getFontScaleFromHeight(
            self.font_face, self.pixel_height, self.thickness)

        self.bg_color = (0, 0, 0)
        self.text_color = (0, 215, 255)
        self.msg_offset = 0
        self.next_img = None
        self.ts = TextureStage.get_default()

    def create_image(self, msg):
        img = np.zeros(self.size.arr, dtype=np.uint8)

        msg = msg + '  '
        (width, _), _ = cv2.getTextSize(msg, self.font_face, self.scale, self.thickness)
        msg_cnt = self.size.x // width
        spaces = self.size.x - msg_cnt * width
        x = 0

        for i in range(msg_cnt):
            cv2.putText(
                img,
                msg,
                (x, 300),
                self.font_face,
                self.scale,
                self.text_color,
                thickness=self.thickness
            )
            x += width + (spaces + i) // msg_cnt

        img = cv2.rotate(img, cv2.ROTATE_180)
        img = cv2.flip(img, 1)
        self.msg_top, self.msg_btm = self.get_min_max_rows(img, self.text_color)

        return img

    def move_letters(self, dt):
        self.msg_offset += dt * 0.1
        if self.msg_offset > 1:
            self.msg_offset = 0

        uv = (self.msg_offset, 0)
        self.model.set_tex_offset(self.ts, uv)

    def delete_msg(self, row_cnt):
        """row_cnt: must be 0 or more.
        """
        if (self.msg_top - self.msg_btm) < row_cnt * 2:
            return True

        process_rs = set(
            [self.msg_top - row_cnt, self.msg_btm + row_cnt]
        )

        for process_r in process_rs:
            start = process_r * self.size.row_length
            end = start + self.size.row_length
            li = self.bg_color * self.size.x
            self.mem_view[start:end] = struct.pack('B' * len(li), *li)

        self.update_image()

    def display_msg(self, row_cnt):
        """row_cnt: must be 0 or more.
        """
        if (n := (self.msg_top - self.msg_btm) // 2 - row_cnt) < 0:
            self.next_img = None
            return True

        process_rs = set(
            [self.msg_btm + n, self.msg_top - n]
        )

        for process_r in process_rs:
            start = process_r * self.size.row_length
            end = start + self.size.row_length
            li = self.next_img[start:end]
            self.mem_view[start:end] = struct.pack('B' * len(li), *li)
            self.update_image()

    def prepare_for_display(self, msg):
        img = self.create_image(msg)
        self.next_img = np.ravel(img)


class CircularDisplay(Ticker):

    def __init__(self, model, size, msg, outer=True):
        super().__init__(model, size, msg, outer=outer)

    def display_settings(self, outer):
        self.font_face = cv2.FONT_HERSHEY_DUPLEX
        self.pixel_height = 60
        self.thickness = 3

        self.scale = cv2.getFontScaleFromHeight(
            self.font_face, self.pixel_height, self.thickness)

        self.bg_color = (255, 0, 0)
        self.text_color = (255, 255, 255)
        self.line_color = (255, 105, 65)

        self.outer = outer
        self.speed = 10 if self.outer else -10
        self.next_img = None

    def create_image(self, msg, lines=True):
        img = np.zeros(self.size.arr, dtype=np.uint8)
        img[:, :, 0] = self.bg_color[0]

        msg = msg + ' '
        (width, _), _ = cv2.getTextSize(msg, self.font_face, self.scale, self.thickness)
        msg_cnt = self.size.x // width
        spaces = self.size.x - msg_cnt * width
        x = 0

        for i in range(msg_cnt):
            cv2.putText(
                img,
                msg,
                (x, 260),
                self.font_face,
                self.scale,
                self.text_color,
                thickness=self.thickness
            )
            x += width + (spaces + i) // msg_cnt

        img = cv2.rotate(img, cv2.ROTATE_180)

        if self.outer:
            img = cv2.flip(img, 1)

        if lines:
            for y in [40, 480]:
                cv2.line(
                    img,
                    (0, y),
                    (self.size.x, y),
                    self.line_color,
                    thickness=6,
                    lineType=cv2.LINE_AA
                )

        self.msg_top, self.msg_btm = self.get_min_max_rows(img, self.text_color)
        return img

    def move_letters(self, dt):
        angle = dt * self.speed
        self.model.set_h(self.model.get_h() - angle)

    def delete_msg(self, row_cnt):
        if (process_r := self.msg_btm + row_cnt) > self.msg_top or \
                process_r < self.msg_btm:
            return True

        start = process_r * self.size.row_length
        end = start + self.size.row_length
        # struct is faster than ndarray.
        li = [255, 0, 0] * self.size.x
        self.mem_view[start:end] = struct.pack('B' * len(li), *li)
        self.update_image()
        # self.mem_view[start:end] = np.array([255, 0, 0] * self.size.x, dtype=np.uint8)

    def display_msg(self, row_cnt):
        if (process_r := self.msg_top - row_cnt) < self.msg_btm or \
                process_r > self.msg_top:
            self.next_img = None
            return True

        start = process_r * self.size.row_length
        end = start + self.size.row_length
        li = self.next_img[start:end]
        self.mem_view[start:end] = struct.pack('B' * len(li), *li)
        self.update_image()

    def prepare_for_display(self, msg):
        img = self.create_image(msg, lines=False)
        self.next_img = np.ravel(img)


class VerticalDisplay(Ticker):

    def __init__(self, model, size, msg):
        super().__init__(model, size, msg)

    def display_settings(self):
        self.thickness = 0
        self.pixel_height = 300
        self.font_face = ImageFont.truetype('fonts/Mohave-Bold.ttf', self.pixel_height)

        self.bg_color = (0, 0, 0)
        self.text_color = (0, 215, 255)
        self.pixels = 2000
        self.next_img = None
        self.text_elems = None
        self.msg_offset = 0
        self.ts = TextureStage.get_default()

    def create_image(self, msg):
        img = np.zeros(self.size.arr, dtype=np.uint8)
        img_pl = Image.fromarray(img)
        draw = ImageDraw.Draw(img_pl)

        msg = msg + ' '
        width = int(draw.textlength(msg, self.font_face))
        msg_cnt = self.size.x // width
        spaces = self.size.x - msg_cnt * width
        x = 0

        for i in range(msg_cnt):
            draw.text(
                (x, 80),
                msg,
                fill=self.text_color,
                font=self.font_face,
                stroke_width=self.thickness
            )
            x += width + (spaces + i) // msg_cnt

        img_pl = ImageOps.flip(img_pl)
        img = np.array(img_pl)
        return img

    def replace_color(self, cnt, color):
        if cnt > len(self.text_elems):
            self.text_elems = None
            return 0

        for r, c in self.text_elems[cnt:cnt + self.pixels]:
            idx = r * self.size.row_length + c * 3

            for i in range(self.size.z):
                self.mem_view[idx + i] = color[i]

        self.update_image()
        return self.pixels

    def delete_msg(self, cnt):
        return self.replace_color(cnt, self.bg_color)

    def display_msg(self, cnt):
        return self.replace_color(cnt, self.text_color)

    def move_letters(self, dt):
        self.msg_offset += dt * 0.1
        if self.msg_offset > 1:
            self.msg_offset = 0

        uv = (self.msg_offset, 0)
        self.model.set_tex_offset(self.ts, uv)

    def find_text_elements(self, img):
        idxes = np.where(~np.all(img == self.bg_color, axis=2))
        text_elems = list(zip(idxes[0], idxes[1]))
        random.shuffle(text_elems)
        return text_elems

    def prepare_for_deletion(self):
        img = np.asarray(self.mem_view).reshape(self.size.arr)
        self.text_elems = self.find_text_elements(img)

    def prepare_for_display(self, msg):
        img = self.create_image(msg)
        self.text_elems = self.find_text_elements(img)
        self.next_img = np.ravel(img)