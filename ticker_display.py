import struct
from enum import Enum, auto
from typing import NamedTuple

import cv2
import numpy as np

from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, Vec3, LColor
from panda3d.core import Texture


class TickerDisplay:

    def __init__(self, model, size, font_face, pixel_height, thickness, text_color):
        self.model = model
        self.size = size
        self.font_face = font_face
        self.pixel_height = pixel_height
        self.thickness = thickness
        self.text_color = text_color        
        self.next_img = None

        self.tex = Texture('image')
        self.tex.setup_2d_texture(
            self.size.x,
            self.size.y,
            Texture.T_unsigned_byte,
            Texture.F_rgb
        )
        