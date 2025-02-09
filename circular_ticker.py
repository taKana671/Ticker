import struct

import cv2
import numpy as np

from panda3d.core import NodePath
from panda3d.core import Point3, Vec3, LColor
from panda3d.core import Texture

from base_ticker import Process, Size, BaseTicker
from models import CylinderModel


class TickerDisplay:

    def __init__(self, model, size, msg, pixel_height=60, thickness=3, outer=True):
        self.model = model
        self.size = size  # 256 * 20, 256 * 2, 3
        self.outer = outer
        self.font_face = cv2.FONT_HERSHEY_DUPLEX
        self.thickness = thickness
        self.scale = cv2.getFontScaleFromHeight(
            self.font_face, pixel_height, self.thickness)

        self.bg_color = (255, 0, 0)
        self.text_color = (255, 255, 255)
        self.line_color = (255, 105, 65)
        self.speed = 10
        self.next_img = None

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

    def get_min_max_rows(self, img):
        idxes = np.where(np.all(img == self.text_color, axis=2))[0]
        return idxes[-1], idxes[0]

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

        self.msg_top, self.msg_btm = self.get_min_max_rows(img)
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
        self.setup_image()
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
        self.setup_image()

    def setup_image(self):
        self.tex.set_ram_image(self.mem_view)
        self.model.clear_color()
        self.model.set_texture(self.tex)

    def prepare_for_display(self, msg):
        img = self.create_image(msg, lines=False)
        self.next_img = np.ravel(img)


class CircularTicker(BaseTicker):

    def __init__(self, parent, msg, pos, hpr):
        super().__init__('circular_ticker', parent, pos, hpr)
        self.next_msg = None
        self.process = None
        self.counter = 0
        self.create_ticker(msg)

    def create_ticker(self, msg):
        self.ticker_display = NodePath("ticker_display")
        self.ticker_display.reparent_to(self.root)

        framework = NodePath('framework')
        # framework.set_texture(base.loader.load_texture('textures/concrete_01.jpg'))
        framework.set_color(LColor(0.5, 0.5, 0.5, 1.0))
        framework.reparent_to(self.ticker_display)

        rad = 4.48
        inner_rad = 4.08

        model = CylinderModel(
            'frame', radius=rad, inner_radius=inner_rad, height=1, segs_bottom_cap=3, segs_top_cap=3)
        model.reparent_to(framework)

        pole_rad = (rad - inner_rad) / 2
        v = rad - pole_rad
        xy = [(0, -v), (0, v), (-v, 0), (v, 0)]

        for i, (x, y) in enumerate(xy):
            model = CylinderModel(
                f'pole_{i}', radius=pole_rad, height=6, segs_bottom_cap=2, segs_top_cap=2)
            model.set_pos_hpr(Point3(x, y, 0), Vec3(0, 180, 0))
            model.reparent_to(framework)

        ticker = NodePath('ticker')
        # msg = 'Hello everyone! Lets study.'
        size = Size(256 * 20, 256 * 2, 3)
        self.tickers = []

        for i, (rad, is_outer) in enumerate([[4.0, False], [4.5, True]]):
            model = CylinderModel(f'ticker_{i}', radius=rad, height=1)
            model.reparent_to(ticker)
            display = TickerDisplay(model, size, msg, outer=is_outer)
            self.tickers.append(display)

        ticker.reparent_to(self.ticker_display)

    def change_message(self, msg):
        self.process = Process.DELETE
        self.next_msg = msg

    def delete_old_msg(self):
        if all([t.delete_msg(self.counter) for t in self.tickers]):
            self.counter = 0
            return True

        self.counter += 1

    def prepare_new_msg(self):
        for t in self.tickers:
            t.prepare_for_display(self.next_msg)

        self.next_msg = None

    def display_new_msg(self):
        if all([t.display_msg(self.counter) for t in self.tickers]):
            self.counter = 0
            return True

        self.counter += 1

    def rotate_display(self, dt):
        for t in self.tickers:
            t.move_letters(dt)

    def update(self, dt):
        self.rotate_display(dt)

        match self.process:

            case Process.DELETE:
                if self.delete_old_msg():
                    self.process = Process.PREPARE

            case Process.PREPARE:
                self.prepare_new_msg()
                self.process = Process.DISPLAY

            case Process.DISPLAY:
                if self.display_new_msg():
                    self.process = None