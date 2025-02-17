from abc import ABC, abstractmethod
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


class BaseTicker(ABC):

    def __init__(self, name):
        self.root = NodePath(PandaNode(name))
        self.next_msg = None
        self.process = None
        self.counter = 0

    @abstractmethod
    def create_ticker(self, msg):
        """Create ticker.
        """

    @abstractmethod
    def change_message(self, msg):
        """If a message is typed in the entry, starts processing.
        """

    @abstractmethod
    def update(self, dt):
        """Update ticker display.
        """

    def set_pos_hpr(self, pos, hpr):
        self.root.set_pos_hpr(pos, hpr)

    def reparent_to(self, parent):
        self.root.reparent_to(parent)