import struct
from enum import Enum, auto
from typing import NamedTuple

import cv2
import numpy as np

from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, Vec3, LColor, CardMaker
from panda3d.core import Texture, TextureStage
from direct.interval.LerpInterval import LerpTexOffsetInterval
from panda3d.core import Spotlight

from lights import BasicAmbientLight
from shapes.src import Box


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

    def __init__(self, model, size, default_msg, pixel_height=80, thickness=6):
        self.model = model
        self.size = size
        self.font_face = cv2.FONT_HERSHEY_COMPLEX
        # self.font_face = cv2.FONT_HERSHEY_DUPLEX
        self.thickness = thickness
        self.scale = cv2.getFontScaleFromHeight(
            self.font_face, pixel_height, self.thickness)
        self.text_color = (0, 215, 255)

        self.msg_offset = 0
        self.initialize(default_msg)

        self.next_msg = None

    def initialize(self, default_msg):
        self.tex = Texture('image')

        self.tex.setup_2d_texture(
            self.size.x,
            self.size.y,
            Texture.T_unsigned_byte,
            Texture.F_rgb
        )

        repeated_msg = self.repeat_msg(default_msg)
        img = self.create_image(repeated_msg)
        self.tex.set_ram_image(img)
        self.model.set_texture(self.tex)
        self.mem_view = memoryview(self.tex.modify_ram_image())

    # ##########################################################

    def repeat_msg(self, msg):
        msg = msg + '  '
        # cv2.getTextSize returns: (width, height), baseline
        (width, _), _ = cv2.getTextSize(msg, self.font_face, self.scale, self.thickness)
        n = len(msg)                                      # word count of message
        char_w = width // n                               # pixel count of each word
        char_cnt = self.size.x // char_w                  # how many words the ticker can display
        msg_cnt = char_cnt // n                           # repeat count of the message
        x = char_cnt - msg_cnt * n                        # the number of spaces
        li = [(x + i) // msg_cnt for i in range(msg_cnt)]

        repeated_msg = ''
        for num in li:
            repeated_msg += msg + ' ' * num

        return repeated_msg

    def get_min_max_rows(self, img):
        idxes = np.where(np.all(img == self.text_color, axis=2))[0]
        return idxes[-1], idxes[0]

    def create_image(self, msg):
        img = np.zeros(self.size.arr, dtype=np.uint8)

        cv2.putText(
            img,
            msg,
            (0, 300),
            self.font_face,
            self.scale,
            self.text_color,
            thickness=self.thickness
        )
        img = cv2.rotate(img, cv2.ROTATE_180)
        img = cv2.flip(img, 1)
        self.msg_top, self.msg_btm = self.get_min_max_rows(img)

        return img

    # ##########################################################

    def move_letters(self, dt):
        # pass
        self.msg_offset += dt * 0.1
        if self.msg_offset > 1:
            self.msg_offset = 0

        self.model.set_tex_offset(TextureStage.get_default(), (self.msg_offset, 0))

    def del_msg(self, row_cnt):
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
            li = [0, 0, 0] * self.size.x
            self.mem_view[start:end] = struct.pack('B' * len(li), *li)

        self.setup_image()

    def show_msg(self, row_cnt):
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
            self.setup_image()

    def prepare_image(self, msg):
        repeated_msg = self.repeat_msg(msg)
        img = self.create_image(repeated_msg)
        self.next_img = np.ravel(img)

    def setup_image(self):
        self.tex.set_ram_image(self.mem_view)
        self.model.clear_color()
        self.model.set_texture(self.tex)


class SquareTicker(NodePath):

    def __init__(self):
        super().__init__(PandaNode('square_ticker'))
        self.reparent_to(base.render)
        # self.set_pos_hpr(Point3(0, 5, -5), Vec3(90, 0, 0))
        self.set_pos_hpr(Point3(5, 5, -5), Vec3(90, 0, 0))
        self.create_ticker()

        self.next_msg = None
        self.process = None
        self.counter = 0

        ambient_light = BasicAmbientLight()

    def create_ticker(self):
        # make building
        self.building = NodePath('building')
        self.building.reparent_to(self)

        model = BoxModel('building', width=10, depth=10, height=15)
        model.set_texture(base.loader.load_texture('textures/tile_05.jpg'))
        model.reparent_to(self.building)

        # make billboards
        self.billboard = NodePath('billboard')
        self.billboard.set_z(2.5)
        self.billboard.reparent_to(self.building)

        boards = [
            [Point3(0, 5.2, 0), Vec3(180, 0, 0)],
            [Point3(-5.2, 0, 0), Vec3(270, 0, 0)]
        ]

        for pos, hpr in boards:
            card = CardMaker('card')
            card.set_frame(-4, 4, -2, 2)
            board = self.billboard.attach_new_node(card.generate())
            board.set_pos_hpr(pos, hpr)
            board.set_texture(base.loader.load_texture('textures/panda3d_logo_2.png'))
            board.setShaderAuto()

        # make ticker display
        self.ticker = NodePath('ticker')
        model = BoxModel('ticker_display', width=10.5, depth=10.5, height=1, open_top=True, open_bottom=True)
        model.reparent_to(self.ticker)
        self.ticker.set_z(6)
        self.ticker.reparent_to(self.building)

        msg = 'Panda3D'
        size = Size(256 * 12, 256 * 2, 3)
        self.ticker_display = TickerDisplay(model, size, msg)

        spot_light = base.render.attach_new_node(Spotlight('spotlight'))
        spot_light.node().set_color(LColor(1, 1, 1, 1))
        spot_light.node().set_attenuation(Vec3(0, 0, 0.001))
        # spot_light.node().set_attenuation(Vec3(0, 0, 0.1))
        spot_light.node().set_exponent(50)
        # spot_light.node().set_attenuation(Vec3(1, 0, 0))
        # spot_light.node().set_exponent(20)
        spot_light.node().get_lens().set_fov(30)
        spot_light.node().get_lens().set_near_far(1, 10)
        spot_light.set_pos_hpr(self.building, Vec3(-5.6, 0, 8), Vec3(90, -90, 0))
        spot_light.node().show_frustum()
        spot_light.node().set_shadow_caster(True)
        # base.render.set_light(spot_light)
        # base.render.setShaderAuto()
        board.set_light(spot_light)

        # LerpTexOffsetInterval(model, 5, (1, 0), (0, 0)).loop()

    def change_message(self, msg):
        self.process = Process.DELETE
        self.next_msg = msg

    def del_old_msg(self):
        if self.ticker_display.del_msg(self.counter):
            self.counter = 0
            return True

        self.counter += 1

    def prepare_new_msg(self):
        self.ticker_display.prepare_image(self.next_msg)
        self.next_msg = None

    def show_new_msg(self):
        if self.ticker_display.show_msg(self.counter):
            self.counter = 0
            return True

        self.counter += 1

    def update(self, dt):
        self.ticker_display.move_letters(dt)

        match self.process:

            case Process.DELETE:
                if self.del_old_msg():
                    self.process = Process.PREPARE

            case Process.PREPARE:
                self.prepare_new_msg()
                self.process = Process.DISPLAY

            case Process.DISPLAY:
                if self.show_new_msg():
                    self.process = None
