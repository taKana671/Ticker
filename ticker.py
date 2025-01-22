import math

import cv2
import numpy as np
from typing import NamedTuple

from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, Vec3, PTA_uchar, CPTA_uchar, LColor
from panda3d.core import Texture, TextureStage, TransformState, TransparencyAttrib
from direct.interval.IntervalGlobal import Sequence, Func

from shapes.src import Box, Cylinder


class Size(NamedTuple):

    x: int
    y: int


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


class Ticker:

    def __init__(self, model, size, default_msg, height=60, thickness=3, outer=True):
        self.model = model
        self.size = size  # 256 * 20, 256 * 2
        self.outer = outer
        self.face = cv2.FONT_HERSHEY_DUPLEX
        self.height = height
        self.thickness = thickness
        self.scale = cv2.getFontScaleFromHeight(self.face, self.height, self.thickness)
        self.text_color = (255, 255, 255)
        self.line_color = (65, 105, 255)
        self.setup(default_msg)

    def setup(self, default_msg):
        self.model.set_transparency(TransparencyAttrib.M_alpha)
        self.tex = Texture('image')
        self.tex.setup_2d_texture(self.size.x, self.size.y, Texture.T_unsigned_byte, Texture.F_rgb)
        img = self.create_image(default_msg)
        # self.tex.set_ram_image(img)
        self.tex.set_ram_image_as(img, "RGB")
        self.model.set_texture(self.tex)
        self.mem_view = memoryview(self.tex.modify_ram_image())

    def create_image(self, msg):
        msg = msg + '  '
        (width, _), baseline = cv2.getTextSize(msg, self.face, self.scale, self.thickness)

        n = len(msg)                       # word count of message
        char_w = width // n                # pixel count of one word
        char_cnt = self.size.x // char_w   # the word count which ticker can display
        msg_cnt = char_cnt // n            # repeat count of the message
        x = char_cnt - msg_cnt * n
        li = [(x + i) // msg_cnt for i in range(msg_cnt)]

        msgs = ''
        for num in li:
            msgs += msg + ' ' * num

        img = np.zeros((self.size.y, self.size.x, 3), dtype=np.uint8)
        img[:, :, 2] = 255
        cv2.putText(img, msgs, (0, 260), self.face, self.scale, self.text_color, thickness=self.thickness)
        img = cv2.rotate(img, cv2.ROTATE_180)

        if self.outer:
            img = cv2.flip(img, 1)

        cv2.line(img, (0, 40), (self.size.x, 40), self.line_color, thickness=6, lineType=cv2.LINE_AA)
        cv2.line(img, (0, 480), (self.size.x, 480), self.line_color, thickness=6, lineType=cv2.LINE_AA)

        # cv2.imwrite('test.png', arr)
        return img

    def change_image(self, msg):
        img = self.create_image(msg)
        self.mem_view[:] = np.ravel(img)
        # self.tex.set_ram_image(self.mem)
        self.tex.set_ram_image_as(self.mem, "RGB")
        self.model.set_texture(self.tex)


class CircularTicker(NodePath):

    def __init__(self):
        super().__init__(PandaNode('ticker_root'))
        self.reparent_to(base.render)
        self.set_pos(Point3(0, 0, 0))

        self.create_framework()
        self.create_ticker()
        self.ticker.hprInterval(15, Vec3(-360, 0, 0)).loop()

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
        size = Size(256 * 20, 256 * 2)

        model = CylinderModel(radius=4.0, height=1)
        model.reparent_to(self.ticker)
        self.inner = Ticker(model, size, msg, outer=False)

        model = CylinderModel(radius=4.5, height=1)
        model.reparent_to(self.ticker)
        self.outer = Ticker(model, size, msg, outer=True)

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
        Sequence(
            self.outer.colorScaleInterval(2, 0, 1, blendType='easeInOut'),
            Func(self.change_image, msg),
            self.outer.colorScaleInterval(2, 1, 0, blendType='easeInOut')
        ).start()
