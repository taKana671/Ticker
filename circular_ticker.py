import struct
from enum import Enum, auto
from typing import NamedTuple

import cv2
import numpy as np

from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, Vec3, LColor
from panda3d.core import Texture

from shapes.src import Cylinder


class Process(Enum):

    DELETE = auto()
    DISPLAY = auto()


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


class TickerDisplay:

    def __init__(self, model, size, default_msg, pixel_height=60, thickness=3, outer=True):
        self.model = model
        self.size = size  # 256 * 20, 256 * 2, 3
        self.outer = outer
        self.font_face = cv2.FONT_HERSHEY_DUPLEX
        self.thickness = thickness
        self.scale = cv2.getFontScaleFromHeight(
            self.font_face, pixel_height, self.thickness)
        self.text_color = (255, 255, 255)
        self.line_color = (255, 105, 65)
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

        repeated_msg = self.repeat_msg(default_msg)
        img = self.create_image(repeated_msg, lines=True)
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

    # ##########################################################

    def create_image(self, msg, lines=False):
        img = np.zeros(self.size.arr, dtype=np.uint8)
        img[:, :, 0] = 255

        cv2.putText(
            img,
            msg,
            (0, 260),
            self.font_face,
            self.scale,
            self.text_color,
            thickness=self.thickness
        )
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

    def del_msg(self, row_cnt):
        if (process_r := self.msg_btm + row_cnt) > self.msg_top or \
                process_r < self.msg_btm:
            return True

        start = process_r * self.size.row_length
        end = start + self.size.row_length
        # struct is faster than ndarray.
        li = [255, 0, 0] * self.size.x
        self.mem_view[start:end] = struct.pack('B' * len(li), *li)
        # self.mem_view[start:end] = np.array([255, 0, 0] * self.size.x, dtype=np.uint8)
        self.setup_image()

    def show_msg(self, row_cnt):
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

    def prepare_image(self, msg):
        repeated_msg = self.repeat_msg(msg)
        img = self.create_image(repeated_msg)
        self.next_img = np.ravel(img)


class CircularTicker(NodePath):

    def __init__(self):
        super().__init__(PandaNode('circular_ticker'))
        self.reparent_to(base.render)
        self.set_pos(Point3(0, 0, 0))
        self.create_framework()
        self.create_ticker()

        self.process = None
        self.counter = 0

    def create_framework(self):
        self.framework = NodePath("framework")
        rad = 4.48
        inner_rad = 4.08

        ring = CylinderModel(
            radius=rad, inner_radius=inner_rad, height=1, segs_bottom_cap=3, segs_top_cap=3)
        ring.reparent_to(self.framework)
        ring.set_pos(Point3(0, 0, 0))

        pole_rad = (rad - inner_rad) / 2
        v = rad - pole_rad
        xy = [(0, -v), (0, v), (-v, 0), (v, 0)]

        for i, (x, y) in enumerate(xy):
            pole = CylinderModel(radius=pole_rad, height=6, segs_bottom_cap=2, segs_top_cap=2)
            pole.set_pos_hpr(Point3(x, y, 0), Vec3(0, 180, 0))
            pole.reparent_to(self.framework)

        self.framework.set_color(LColor(0.5, 0.5, 0.5, 1.0))
        self.framework.reparent_to(self)

    def create_ticker(self):
        self.ticker = NodePath('ticker')
        msg = 'Hello everyone! Lets study.'
        size = Size(256 * 20, 256 * 2, 3)
        self.ticker_displays = []

        for rad, is_outer in [[4.0, False], [4.5, True]]:
            model = CylinderModel(radius=rad, height=1)
            model.reparent_to(self.ticker)
            display = TickerDisplay(model, size, msg, outer=is_outer)
            self.ticker_displays.append(display)

        self.ticker.reparent_to(self)

    def change_message(self, msg):
        self.process = Process.DELETE

        for t in self.ticker_displays:
            t.prepare_image(msg)

    def del_old_msg(self):
        if all([t.del_msg(self.counter) for t in self.ticker_displays]):
            self.counter = 0
            return True
        self.counter += 1

    def show_new_msg(self):
        if all([t.show_msg(self.counter) for t in self.ticker_displays]):
            self.counter = 0
            return True
        self.counter += 1

    def update(self, dt):
        angle = dt * 20
        # In this case, hprInterval is not good
        self.ticker.set_h(self.ticker.get_h() - angle)

        match self.process:

            case Process.DELETE:
                if self.del_old_msg():
                    self.process = Process.DISPLAY

            case Process.DISPLAY:
                if self.show_new_msg():
                    self.process = None