import struct
from enum import Enum, auto
from typing import NamedTuple
from PIL import Image, ImageFont, ImageDraw, ImageOps

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

    def __init__(self, model, size, default_msg, pixel_height=90, thickness=6):
        self.model = model

        # self.model.set_tex_scale(TextureStage.get_default(), 1, 6)

        self.size = size
        self.font_face = cv2.FONT_HERSHEY_COMPLEX
        path = r"C:\Users\Kanae\Desktop\py312env\Ticker\fonts\Mohave-Bold.ttf"
        self.font_face = ImageFont.truetype(path, 300)
        self.thickness = thickness
        # self.scale = cv2.getFontScaleFromHeight(
        #     self.font_face, pixel_height, self.thickness)
        self.text_color = (0, 215, 255)
        self.msg_offset = 0
        self.initialize(default_msg)
        self.next_img = None

    def initialize(self, default_msg):
        self.tex = Texture('image')

        self.tex.setup_2d_texture(
            self.size.x,
            self.size.y,
            Texture.T_unsigned_byte,
            Texture.F_rgb
        )

        # repeated_msg = self.repeat_msg(default_msg)
        # img = self.create_image(repeated_msg)

        img = self.create_image(default_msg)
        self.tex.set_ram_image(img)
        self.model.set_texture(self.tex)
        self.mem_view = memoryview(self.tex.modify_ram_image())

    # ##########################################################
    def get_min_max_rows(self, img):
        idxes = np.where(np.all(img == self.text_color, axis=2))[0]
        return idxes[-1], idxes[0]

    def repeat_msg(self, msg, draw):
        # msg = msg + ' '
        width = int(draw.textlength(msg, self.font_face))
        n = len(msg)
        char_w = width // n
        char_cnt = self.size.x // char_w
        msg_cnt = char_cnt // n
        x = char_cnt - msg_cnt * n
        # import pdb; pdb.set_trace()
        # msg_cnt = int(self.size.x // w)
        # x = self.size.x - w * msg_cnt
        li = [(x + i) // msg_cnt for i in range(msg_cnt)]
        print(li)
        repeated_msg = ''
        for num in li:
            repeated_msg += msg + ' ' * num
        # return msg + ' ' * 312 + msg + ' ' * 312
        return repeated_msg

    # ##########################################################

    def create_image(self, msg):
        img = np.zeros(self.size.arr, dtype=np.uint8)
        img_pl = Image.fromarray(img)
        draw = ImageDraw.Draw(img_pl)

        msg = msg + ' '
        width = int(draw.textlength(msg, self.font_face))
        msg_cnt = self.size.x // width
        spaces = self.size.x - msg_cnt * width

        for i in range(msg_cnt):
            x = 0 if i == 0 else (spaces + i) // msg_cnt + width * i
            draw.text((x, 80), msg, (0, 215, 255), font=self.font_face)

        img_pl = ImageOps.flip(img_pl)
        # img_pl.save('test.png')
        img = np.array(img_pl)
        self.msg_top, self.msg_btm = self.get_min_max_rows(img)

        return np.array(img)

    def del_msg(self, row_cnt):
        if (process_r := self.msg_btm + row_cnt) > self.msg_top or \
                process_r < self.msg_btm:
            return True

        start = process_r * self.size.row_length
        end = start + self.size.row_length
        # struct is faster than ndarray.
        li = [0, 0, 0] * self.size.x
        self.mem_view[start:end] = struct.pack('B' * len(li), *li)
        # self.mem_view[start:end] = np.array([255, 0, 0] * self.size.x, dtype=np.uint8)
        self.setup_image()

    def setup_image(self):
        self.tex.set_ram_image(self.mem_view)
        self.model.clear_color()
        self.model.set_texture(self.tex)


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
        # make building
        self.building = NodePath('buildong')
        self.building.reparent_to(self)

        model = BoxModel('building', width=5, depth=5, height=10)
        model.set_texture(base.loader.load_texture('textures/tile_05.jpg'))
        model.reparent_to(self.building)

        frame = BoxModel('frame', width=1, depth=1.2, height=5)
        frame.set_texture(base.loader.load_texture('textures/concrete_01.jpg'))
        # frame.set_pos(Point3(-2, -3.24, 2))
        frame.set_pos(Point3(-2, -3.1, 2))
        frame.reparent_to(self.building)

        self.ticker = NodePath('ticker')
        # card = CardMaker('card')
        # card.set_frame(-0.6, 0.6, -2.4, 2.4)
        # model = self.ticker.attach_new_node(card.generate())

        # model = BoxModel('ticker_display', width=0.2, depth=4.8, height=1, open_top=True, open_bottom=True)
        model = BoxModel('ticker_display', width=1.2, depth=4.8, height=1, open_top=True, open_bottom=True)
        model.reparent_to(self.ticker)

        # model.set_color((0, 0, 0, 1))
        # self.ticker.set_pos_hpr(Point3(-0.45, 0, 0.0), Vec3(0, 90, 0))
        self.ticker.set_pos_hpr(Point3(0, 0, 0.0), Vec3(0, 90, 0))
        # self.ticker.set_pos(Point3(-0.59, 0, 0.05))
        self.ticker.reparent_to(frame)

        LerpTexOffsetInterval(model, 5, (1, 0), (0, 0)).loop()
        msg = 'Panda3D'
        size = Size(256 * 10, 256 * 2, 3)
        self.ticker_display = TickerDisplay(model, size, msg)

    def change_message(self, msg):
        self.process = Process.DELETE
        self.next_msg = msg

    def del_old_msg(self):
        if self.ticker_display.del_msg(self.counter):
            self.counter = 0
            return True

        self.counter += 1

    def update(self, dt):

        match self.process:

            case Process.DELETE:
                if self.del_old_msg():
                    self.process = None

            case Process.PREPARE:
                pass

            case Process.DISPLAY:
                pass

