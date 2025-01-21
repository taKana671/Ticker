import math

import cv2
import numpy as np

from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, Vec3, PTA_uchar, CPTA_uchar, LColor
from panda3d.core import Texture, TextureStage, TransformState, TransparencyAttrib
from direct.interval.IntervalGlobal import Sequence, Func

from shapes.src import Box, Cylinder


class CylinderModel(NodePath):

    def __init__(self, radius=2, inner_radius=0, height=1):
        super().__init__(PandaNode('cylinder'))
        self.model = Cylinder(
            radius=radius,
            inner_radius=inner_radius,
            height=height,
            segs_top_cap=0,
            segs_bottom_cap=0
        ).create()

        self.model.reparent_to(self)
        self.height = height
        self.circumference = radius * 2 * math.pi


class Ticker(NodePath):

    def __init__(self):
        super().__init__(PandaNode('ticker_root'))
        self.reparent_to(base.render)
        self.set_pos(Point3(0, 0, 0))

        self.create_ticker()
        self.hprInterval(10, Vec3(-360, 0, 0)).loop()

    def create_ticker(self):
        self.board = CylinderModel(radius=3.9, height=1.2)
        # self.board = CylinderModel(radius=2, height=1)
        self.board.set_texture(base.loader.load_texture('textures/concrete_01.jpg'))
        self.board.reparent_to(self)
        self.board.set_pos(Point3(0, 0, 0))

        self.outer = CylinderModel(radius=4.0, height=1.1)
        self.outer.reparent_to(self)
        self.outer.set_pos(Point3(0, 0, 0))
        self.outer.set_transparency(TransparencyAttrib.M_alpha)

        msg = 'Hello everyone! Lets study.'
        img = self.create_image(msg)
        self.tex = Texture('image')
        self.tex.setup_2d_texture(
            256 * 20, 256 * 2, Texture.T_unsigned_byte, Texture.F_rgb)
        self.tex.set_ram_image(img)
        # self.tex.set_ram_image_as(arr, "RGB")
        self.outer.set_texture(self.tex)
        self.mem = memoryview(self.tex.modify_ram_image())

    def create_image(self, msg):
        # msg = msg[::-1]
        msg = msg + '  '

        face = cv2.FONT_HERSHEY_DUPLEX
        height = 50
        thickness = 3
        scale = cv2.getFontScaleFromHeight(face, height, thickness)
        (width, _), baseline = cv2.getTextSize(msg, face, scale, thickness)

        n = len(msg)                    # word count of message
        char_w = width // n             # pixel count of one word
        char_cnt = 256 * 20 // char_w   # the word count which ticker can display
        msg_cnt = char_cnt // n         # repeat count of the message
        x = char_cnt - msg_cnt * n
        li = [(x + i) // msg_cnt for i in range(msg_cnt)]

        # length = 256 * 20
        # n = length // width
        # x = length - n * width
        # li = [(x + i) // n for i in range(n)]
        msgs = ''
        for num in li:
            msgs += msg + ' ' * num

        # cnt = (256 * 20) // width
        # msg *= cnt

        arr_1 = np.zeros((256, 256 * 20, 3), dtype=np.uint8)
        arr_1[:, :, 0] = 255

        arr_2 = np.zeros((256, 256 * 20, 3), dtype=np.uint8)
        arr_2[:, :, 0] = 255
        cv2.putText(arr_2, msgs, (0, 100), face, scale, (255, 255, 255), thickness=thickness)
        arr_2 = cv2.rotate(arr_2, cv2.ROTATE_180)
        arr_2 = cv2.flip(arr_2, 1)

        img = np.concatenate([arr_2, arr_1])
        cv2.imwrite('test.png', img)
        return img

    def change_image(self, msg):
        img = self.create_image(msg)
        self.mem[:] = np.ravel(img)
        self.tex.set_ram_image(self.mem)
        # self.tex.set_ram_image_as(self.mem, "RGB")
        self.outer.set_texture(self.tex)

    def change_message(self, msg):
        Sequence(
            self.outer.colorScaleInterval(2, 0, 1, blendType='easeInOut'),
            Func(self.change_image, msg),
            self.outer.colorScaleInterval(2, 1, 0, blendType='easeInOut')
        ).start()


