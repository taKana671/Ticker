import struct
from enum import Enum, auto
from typing import NamedTuple

import cv2
import numpy as np

from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, Vec3, LColor
from panda3d.core import Texture

from shapes.src import Box


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


class SquareTicker(NodePath):

    def __init__(self):
        super().__init__(PandaNode('square_ticker'))
        self.reparent_to(base.render)
        self.set_pos_hpr(Point3(0, 0, -2), Vec3(90, 0, 0))
        self.create_ticker()

    def create_ticker(self):
        self.building = NodePath('building')
        self.building.reparent_to(self)

        model = BoxModel('building', width=6, depth=6, height=10)
        # model.set_pos_hpr(Point3(0, 0, -2), Vec3(90, 0, 0))
        model.reparent_to(self.building)
        model.set_texture(base.loader.load_texture('textures/tile_05.jpg'))
        

        self.ticker = NodePath('ticker')
        model = BoxModel('ticker', width=6.5, depth=6.5, height=1, open_top=True, open_bottom=True)
        model.reparent_to(self.ticker)
        model.set_color(0, 0, 0, 0)
        self.ticker.set_pos(0, 0, 3)
        self.ticker.reparent_to(self)




