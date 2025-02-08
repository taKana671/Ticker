import random
import struct
from enum import Enum, auto
from typing import NamedTuple
from PIL import Image, ImageFont, ImageDraw, ImageOps

from datetime import datetime

import cv2
import numpy as np

from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, Vec3, LColor, CardMaker
from panda3d.core import Texture, TextureStage
from direct.interval.LerpInterval import LerpTexOffsetInterval
from panda3d.core import Spotlight
from panda3d.core import PNMImage, PNMTextMaker

from shapes.src import Box, Plane


class Process(Enum):

    DELETE = auto()
    DISPLAY = auto()
    PREPARE = auto()


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


class BoxModel(NodePath):

    def __init__(self, name, width, depth, height, **open_sides):
        super().__init__(PandaNode(name))
        self.model = Box(
            width=width,
            depth=depth,
            height=height,
            **open_sides
        ).create()

        self.model.reparent_to(self)


class TickerDisplay:

    def __init__(self, model, size, msg, pixel_height=300, thickness=0):
        self.model = model
        self.size = size
        self.font_face = ImageFont.truetype('fonts/Mohave-Bold.ttf', pixel_height)
        self.thickness = thickness

        self.bg_color = (0, 0, 0)
        self.text_color = (0, 215, 255)
        self.pixels = 2000
        self.next_img = None
        self.text_elems = None
        self.msg_offset = 0
        self.ts = TextureStage.get_default()

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

        self.setup_image()
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

    def setup_image(self):
        self.tex.set_ram_image(self.mem_view)
        self.model.clear_color()
        self.model.set_texture(self.tex)

    def prepare_for_deletion(self):
        img = np.asarray(self.mem_view).reshape(self.size.arr)
        self.text_elems = self.find_text_elements(img)

    def prepare_for_display(self, msg):
        img = self.create_image(msg)
        self.text_elems = self.find_text_elements(img)
        self.next_img = np.ravel(img)


class VerticalTicker(NodePath):

    def __init__(self):
        super().__init__(PandaNode('vertical_ticker'))
        self.reparent_to(base.render)
        self.set_pos_hpr(Point3(5, 0, -3), Vec3(0, 0, 0))
        self.create_ticker()

        self.process = None
        self.next_msg = None
        self.counter = 0

    def create_ticker(self):
        self.building = NodePath('buildong')
        self.building.reparent_to(self)

        model = BoxModel('building', width=5, depth=5, height=10)
        model.set_texture(base.loader.load_texture('textures/tile_05.jpg'))
        model.reparent_to(self.building)

        frame = BoxModel('frame', width=1, depth=1.2, height=5)
        frame.set_texture(base.loader.load_texture('textures/concrete_01.jpg'))
        frame.set_pos(Point3(-2, -3.1, 2))
        frame.reparent_to(self.building)

        ticker = NodePath('ticker')
        model = BoxModel('ticker_display', width=1.2, depth=4.8, height=1, open_top=True, open_bottom=True)
        model.reparent_to(ticker)
        ticker.set_pos_hpr(Point3(0, 0, 0), Vec3(0, 90, 0))   # Point3(-0.45, 0, 0.0)
        ticker.reparent_to(frame)

        msg = 'Panda3D'
        size = Size(256 * 10, 256 * 2, 3)
        self.ticker = TickerDisplay(model, size, msg)
        # LerpTexOffsetInterval(model, 5, (1, 0), (0, 0)).loop()

    def change_message(self, msg):
        self.ticker.prepare_for_deletion()
        self.process = Process.DELETE
        self.next_msg = msg

    def prepare_new_msg(self):
        self.ticker.prepare_for_display(self.next_msg)
        self.next_msg = None

    def delete_old_msg(self):
        if (ret := self.ticker.delete_msg(self.counter)) == 0:
            self.counter = ret
            return True

        self.counter += ret

    def display_new_msg(self):
        if (ret := self.ticker.display_msg(self.counter)) == 0:
            self.counter = ret
            return True

        self.counter += ret

    def update(self, dt):
        self.ticker.move_letters(dt)

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
