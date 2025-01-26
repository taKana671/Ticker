import math
import struct
from enum import Enum, auto

import cv2
import numpy as np
from typing import NamedTuple
from datetime import datetime

from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, Vec3, PTA_uchar, CPTA_uchar, LColor
from panda3d.core import Texture, TextureStage, TransformState, TransparencyAttrib
from direct.interval.IntervalGlobal import Sequence, Parallel, Func
from panda3d.core import GeomEnums
from direct.interval.LerpInterval import LerpFunc

from shapes.src import Box, Cylinder


class Process(Enum):

    FADE_OUT = auto()
    FADE_IN = auto()


class Size(NamedTuple):

    x: int
    y: int
    z: int

    @property
    def arr(self):
        return (self.y, self.x, self.z)

    @property
    def row_length(self):
        return self.x * self.z


class CylinderModel(NodePath):

    def __init__(self, radius, inner_radius=0, height=1, segs_top_cap=0, segs_bottom_cap=0):
        super().__init__(PandaNode('cylinder'))
        self.model = Cylinder(
            radius=radius,
            inner_radius=inner_radius,
            height=height,
            segs_top_cap=segs_top_cap,
            segs_bottom_cap=segs_bottom_cap).create()

        self.model.reparent_to(self)
        self.height = height
        self.circumference = radius * 2 * math.pi


class TickerDisplay:

    def __init__(self, model, size, default_msg, height=60, thickness=3, outer=True):
        self.model = model
        self.size = size  # 256 * 20, 256 * 2, 3
        self.outer = outer
        self.face = cv2.FONT_HERSHEY_DUPLEX
        self.height = height
        self.thickness = thickness
        self.scale = cv2.getFontScaleFromHeight(self.face, self.height, self.thickness)
        self.text_color = (255, 255, 255)
        self.line_color = (65, 105, 255)
        self.setup(default_msg)

        self.process_row = None
        self.call_cnt = 0
        self.tota_t = 0

    def setup(self, default_msg):
        # self.model.set_transparency(TransparencyAttrib.M_alpha)
        self.tex = Texture('image')
        self.tex.setup_2d_texture(self.size.x, self.size.y, Texture.T_unsigned_byte, Texture.F_rgb)

        # self.tex.setup_buffer_texture(   # ←これだめ。多分shaderと使う
        #     self.size.x * self.size.y, Texture.T_unsigned_byte, Texture.F_rgb, GeomEnums.UH_static)
        img = self.create_image(default_msg)
        # self.tex.set_ram_image(img)
        self.tex.set_ram_image_as(img, "RGB")
        self.model.set_texture(self.tex)
        self.mem_view = memoryview(self.tex.modify_ram_image())

    def create_image(self, msg):
        msg = msg + '  '
        (width, height), baseline = cv2.getTextSize(msg, self.face, self.scale, self.thickness)
        n = len(msg)                       # word count of message
        char_w = width // n                # pixel count of one word
        char_cnt = self.size.x // char_w   # the word count which ticker can display
        msg_cnt = char_cnt // n            # the repeat count of the message
        x = char_cnt - msg_cnt * n
        li = [(x + i) // msg_cnt for i in range(msg_cnt)]

        msgs = ''
        for num in li:
            msgs += msg + ' ' * num

        msg_y = 260
        self.msg_btm = msg_y - baseline - 4
        self.msg_top = msg_y + height
        # print(self.msg_top, self.msg_btm)

        img = np.zeros((self.size.y, self.size.x, 3), dtype=np.uint8)
        img[:, :, 2] = 255
        cv2.putText(img, msgs, (0, msg_y), self.face, self.scale, self.text_color, thickness=self.thickness)
        img = cv2.rotate(img, cv2.ROTATE_180)

        if self.outer:
            img = cv2.flip(img, 1)

        for y in [40, 480]:
            cv2.line(img, (0, y), (self.size.x, y), self.line_color, thickness=6, lineType=cv2.LINE_AA)

        # cv2.imwrite('test.png', arr)
        return img

    def change_image(self, msg):
        img = self.create_image(msg)
        self.mem_view[:] = np.ravel(img)
        # self.tex.set_ram_image(self.mem)
        self.tex.set_ram_image_as(self.mem_view, "RGB")
        self.model.clear_color()
        self.model.set_texture(self.tex)
        # LerpFunc

    def del_msg_per_row(self, row_cnt):
        if (process_r := self.msg_btm + row_cnt) < self.msg_btm or \
                process_r > self.msg_top:
            return True

        # start = int(r) * self.size.row_length
        start = process_r * self.size.row_length
        end = start + self.size.row_length

        # self.mem_view[start:end] = np.array([255, 0, 0] * self.size.x, dtype=np.uint8)
        li = [255, 0, 0] * self.size.x
        self.mem_view[start:end] = struct.pack('B' * len(li), *li)

        self.tex.set_ram_image(self.mem_view)
        self.model.clear_color()
        self.model.set_texture(self.tex)

        # took = datetime.now() - dt
        # self.tota_t += took.microseconds
        # avg = self.tota_t / self.call_cnt
        # print(f'fade out tooks {took}., avg: {avg}')

    def change_message(self, msg):
        pass


class CircularTicker(NodePath):

    def __init__(self):
        super().__init__(PandaNode('ticker_root'))
        self.reparent_to(base.render)
        self.set_pos(Point3(0, 0, 0))

        self.create_framework()
        self.create_ticker()
        # self.ticker.hprInterval(15, Vec3(-360, 0, 0)).loop()

        self.process = None
        self.is_msg_change = False
        self.counter = 0

    def create_framework(self):
        self.framework = NodePath("framework")
        self.framework.reparent_to(self)

        rad = 4.48
        inner_rad = 4.08

        ring = CylinderModel(
            radius=rad, inner_radius=inner_rad, height=1, segs_bottom_cap=3, segs_top_cap=3)
        ring.set_color(LColor(0.5, 0.5, 0.5, 1.0))
        ring.reparent_to(self.framework)
        ring.set_pos(Point3(0, 0, 0))

        pole_rad = (rad - inner_rad) / 2
        n = rad - pole_rad
        xy = [(0, -n), (0, n), (-n, 0), (n, 0)]

        for i, (x, y) in enumerate(xy):
            pole = CylinderModel(radius=pole_rad, height=6, segs_bottom_cap=2, segs_top_cap=2)
            pole.set_color(LColor(0.5, 0.5, 0.5, 1.0))
            pole.set_pos_hpr(Point3(x, y, 0), Vec3(0, 180, 0))
            pole.reparent_to(self.framework)

    def create_ticker(self):
        self.ticker = NodePath('ticker')
        self.ticker.reparent_to(self)
        msg = 'Hello everyone! Lets study.'
        size = Size(256 * 20, 256 * 2, 3)
        self.ticker_displays = []

        for rad, is_outer in [[4.0, False], [4.5, True]]:
            model = CylinderModel(radius=rad, height=1)
            model.reparent_to(self.ticker)
            display = TickerDisplay(model, size, msg, outer=is_outer)
            self.ticker_displays.append(display)


        # model = CylinderModel(radius=4.0, height=1)
        # model.reparent_to(self.ticker)
        # self.inner = Ticker(model, size, msg, outer=False)

        # model = CylinderModel(radius=4.5, height=1)
        # model.reparent_to(self.ticker)
        # self.outer = Ticker(model, size, msg, outer=True)

        # self.inner = CylinderModel(radius=4.0, height=1)
        # self.inner.reparent_to(self.ticker)
        # self.set_pos(0, 0, 0)
        # self.inner.set_transparency(TransparencyAttrib.M_alpha)
        # img = self.create_image(msg, outer=False)
        # self.tex_inner = Texture('image')
        # self.tex_inner.setup_2d_texture(
        #     256 * 20, 256 * 2, Texture.T_unsigned_byte, Texture.F_rgb)
        # self.tex_inner.set_ram_image(img)
        # # self.tex.set_ram_image_as(arr, "RGB")
        # self.inner.set_texture(self.tex_inner)

        # self.outer = CylinderModel(radius=4.5, height=1)
        # self.outer.reparent_to(self.ticker)
        # self.outer.set_pos(Point3(0, 0, 0))
        # self.outer.set_transparency(TransparencyAttrib.M_alpha)

        # img = self.create_image(msg)
        # self.tex = Texture('image')
        # self.tex.setup_2d_texture(
        #     256 * 20, 256 * 2, Texture.T_unsigned_byte, Texture.F_rgb)
        # self.tex.set_ram_image(img)
        # # self.tex.set_ram_image_as(arr, "RGB")
        # self.outer.set_texture(self.tex)
        # self.mem = memoryview(self.tex.modify_ram_image())


    def change_message(self, msg):
        self.process = Process.FADE_OUT
        self.counter = 0
        self.new_msg = msg

    def del_old_msg(self):
        if all([t.del_msg_per_row(self.counter) for t in self.ticker_displays]):
            return True
        self.counter += 1

    def update(self, dt):
        angle = dt * 25
        self.ticker.set_h(self.ticker.get_h() - angle)

        match self.process:

            case Process.FADE_OUT:
                if self.del_old_msg():
                    self.process = Process.FADE_IN

            case Process.FADE_IN:
                for t in self.ticker_displays:
                    t.change_image(self.new_msg)
                self.process = None

        # if self.is_msg_change:
        #     for t in self.ticker_displays:
        #         t.fadeout_msg(self.counter)
        #     self.counter += 1

        #     if self.counter > 320:
        #         self.is_msg_change = False
        #         self.counter = 0