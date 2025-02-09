from enum import Enum, auto
from typing import NamedTuple

from panda3d.core import NodePath, PandaNode


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


class BaseTicker:

    def __init__(self, name, parent, pos, hpr):
        self.root = NodePath(PandaNode(name))
        self.root.set_pos_hpr(pos, hpr)
        self.root.reparent_to(parent)

    def __init_subclass__(cls, *kwargs):
        super().__init_subclass__(*kwargs)
        for method in ('create_ticker', 'change_message', 'update'):
            if method not in cls.__dict__:
                raise NotImplementedError(f"Subclasses must implement the {method} method.")