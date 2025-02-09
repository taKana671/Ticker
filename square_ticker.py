import struct

import cv2
import numpy as np

from panda3d.core import NodePath
from panda3d.core import Point3, Vec3, LColor, CardMaker
from panda3d.core import Texture, TextureStage
# from direct.interval.LerpInterval import LerpTexOffsetInterval

from base_ticker import Process, Size, BaseTicker
from models import BoxModel


class TickerDisplay:

    def __init__(self, model, size, msg, pixel_height=80, thickness=6):
        self.model = model
        self.size = size
        self.font_face = cv2.FONT_HERSHEY_COMPLEX
        self.thickness = thickness
        self.scale = cv2.getFontScaleFromHeight(
            self.font_face, pixel_height, self.thickness)

        self.bg_color = (0, 0, 0)
        self.text_color = (0, 215, 255)
        self.msg_offset = 0
        self.next_img = None
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
        self.msg_top, self.msg_btm = self.get_min_max_rows(img)

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

        self.setup_image()

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
            self.setup_image()

    def setup_image(self):
        self.tex.set_ram_image(self.mem_view)
        self.model.clear_color()
        self.model.set_texture(self.tex)

    def prepare_for_display(self, msg):
        img = self.create_image(msg)
        self.next_img = np.ravel(img)


class SquareTicker(BaseTicker):

    def __init__(self, parent, msg, pos, hpr):
        super().__init__('square_ticker', parent, pos, hpr)
        self.next_msg = None
        self.process = None
        self.counter = 0
        self.create_ticker(msg)

    def create_ticker(self, msg):
        # make building
        self.building = NodePath('building')
        self.building.reparent_to(self.root)

        model = BoxModel('building', width=10, depth=10, height=15)
        model.set_texture(base.loader.load_texture('textures/tile_05.jpg'))
        model.reparent_to(self.building)

        # make billboards
        billboard = NodePath('billboard')
        billboard.set_z(2.5)
        billboard.reparent_to(self.building)

        boards = [
            [Point3(0, 5.2, 0), Vec3(180, 0, 0)],
            [Point3(-5.2, 0, 0), Vec3(270, 0, 0)]
        ]

        for pos, hpr in boards:
            card = CardMaker('card')
            card.set_frame(-4, 4, -2, 2)
            board = billboard.attach_new_node(card.generate())
            board.set_pos_hpr(pos, hpr)
            board.set_texture(base.loader.load_texture('textures/panda3d_logo_2.png'))
            # board.setShaderAuto()

        # make ticker display
        ticker = NodePath('ticker')
        model = BoxModel('ticker_display', width=10.5, depth=10.5, height=1, open_top=True, open_bottom=True)
        model.reparent_to(ticker)
        ticker.set_z(6)
        ticker.reparent_to(self.building)

        # msg = 'Panda3D'
        size = Size(256 * 12, 256 * 2, 3)
        self.ticker = TickerDisplay(model, size, msg)
        # LerpTexOffsetInterval(model, 5, (1, 0), (0, 0)).loop()

    def change_message(self, msg):
        self.process = Process.DELETE
        self.next_msg = msg

    def delete_old_msg(self):
        if self.ticker.delete_msg(self.counter):
            self.counter = 0
            return True

        self.counter += 1

    def prepare_new_msg(self):
        self.ticker.prepare_for_display(self.next_msg)
        self.next_msg = None

    def display_new_msg(self):
        if self.ticker.display_msg(self.counter):
            self.counter = 0
            return True

        self.counter += 1

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



# spot_light = base.render.attach_new_node(Spotlight('spotlight'))
# spot_light.node().set_color(LColor(1, 1, 1, 1))
# spot_light.node().set_attenuation(Vec3(0, 0, 0.001))
# # spot_light.node().set_attenuation(Vec3(0, 0, 0.1))
# spot_light.node().set_exponent(50)
# # spot_light.node().set_attenuation(Vec3(1, 0, 0))
# # spot_light.node().set_exponent(20)
# spot_light.node().get_lens().set_fov(30)
# spot_light.node().get_lens().set_near_far(1, 10)
# spot_light.set_pos_hpr(self.building, Vec3(-5.6, 0, 8), Vec3(90, -90, 0))
# spot_light.node().show_frustum()
# spot_light.node().set_shadow_caster(True)
# # base.render.set_light(spot_light)
# # base.render.setShaderAuto()
# board.set_light(spot_light)