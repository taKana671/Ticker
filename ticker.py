import math

import cv2
import numpy as np

from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, Vec3, PTA_uchar, CPTA_uchar, LColor
from panda3d.core import Texture, TextureStage, TransformState

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
        self.create_texture()
        self.hprInterval(10, Vec3(-360, 0, 0)).loop()

    def create_ticker(self):
        self.board = CylinderModel(radius=1.9, height=1.2)
        self.board.set_texture(base.loader.load_texture('textures/concrete_01.jpg'))
        self.board.reparent_to(self)
        self.board.set_pos(Point3(0, 0, 0))

        self.outer = CylinderModel(radius=2.0, height=1.0)
        self.outer.reparent_to(self)
        # self.outer.set_transform(TransformState.make_hpr(Vec3(0, 180, 0)))
        self.outer.set_pos(Point3(0, 0, 0.1))
        # self.outer.set_pos_hpr(Point3(0, 0, 0), Vec3(0, 360, 0))

    def create_texture(self):
        arr_1 = np.zeros((256, 256 * 5, 3), dtype=np.uint8)
        arr_1[:, :, 0] = 255
        # cv2.putText(arr_1, 'JIHGFEDCBA', (50, 20), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255))
        self.tex = Texture('image')

        arr = np.zeros((256, 256 * 5, 3), dtype=np.uint8)
        arr[:, :, 0] = 255
        msg = 'Hello everyone! Lets study.'
        # msg = msg[::-1]
        cv2.putText(arr, msg, (0, 100), cv2.FONT_HERSHEY_DUPLEX, 1.5, (255, 255, 255), thickness=2)
        arr = cv2.rotate(arr, cv2.ROTATE_180)
        arr = cv2.flip(arr, 1)

        arr = np.concatenate([arr, arr_1])
        cv2.imwrite('test.png', arr)

        self.tex = Texture('image')
        self.tex.setup_2d_texture(
            256*5, 256* 2, Texture.T_unsigned_byte, Texture.F_rgb)
        # self.tex.set_ram_image(arr)
        self.tex.set_ram_image_as(arr, "RGB")

        ts = TextureStage('ts')
        self.outer.set_texture(self.tex)
        # self.outer.set_tex_offset(TextureStage.get_default(), 20, -10)

        
        # ************************************************
        # arr = np.zeros((256, 256, 3), dtype=np.uint8)
        # arr[:, :, 0] = 255
        # cv2.putText(arr, 'ABCDEFGHIJ', (20, 50), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255))
        # self.tex = Texture('image')
        # self.tex.setup_2d_texture(256, 256, Texture.T_unsigned_byte, Texture.F_rgb)
        # # self.tex.set_ram_image(arr)
        # self.tex.set_ram_image_as(arr, "RGB")
        # self.model.set_texture(self.tex)
        # # self.mem = memoryview(arr)
        # # self.mem = memoryview(self.tex.modify_ram_image())
        # ************************************************

    def change_message(self):
        pass
        # if self.color_change:
        #     # arr = np.zeros((256, 256, 3), dtype=np.uint8)
        #     # arr[:, :, 1] = 255
        #     # cv2.putText(arr, 'KLMNOPQ', (20, 50), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255))
        #     # self.tex.clear_ram_image()
        #     # self.tex.set_ram_image_as(arr, "RGB")
        #     # # self.box.set_texture(self.tex)


        #     # self.mem = memoryview(self.tex.modify_ram_image())
        #     # # self.mem[] = arr
        #     # # import pdb; pdb.set_trace()
        #     # for i in range(len(self.mem)):
        #     #     # import pdb; pdb.set_trace()
        #     #     if i % 3 == 0:
        #     #         self.mem[i] = 255

        #     self.tex.set_ram_image(self.mem)
        #     # self.tex.set_ram_image_as(self.mem, "RGB")
        #     self.model.set_texture(self.tex)
        #     self.color_change = False