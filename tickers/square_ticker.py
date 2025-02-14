from panda3d.core import NodePath
from panda3d.core import Point3, Vec3, CardMaker
# from direct.interval.LerpInterval import LerpTexOffsetInterval

from .base_ticker import Process, Size, BaseTicker
from .ticker_displays import SquareDisplay
from .models import BoxModel


class SquareTicker(BaseTicker):

    def __init__(self, msg):
        super().__init__('square_ticker')
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
            board.set_texture(base.loader.load_texture('textures/panda3d_logo.png'))
            # board.setShaderAuto()

        # make ticker display
        ticker = NodePath('ticker')
        model = BoxModel('ticker_display', width=10.5, depth=10.5, height=1, open_top=True, open_bottom=True)
        model.reparent_to(ticker)
        ticker.set_z(6)
        ticker.reparent_to(self.building)

        size = Size(256 * 12, 256 * 2, 3)
        self.ticker = SquareDisplay(model, size, msg)
        # LerpTexOffsetInterval(model, 5, (1, 0), (0, 0)).loop()

    def change_message(self, msg):
        if not self.process:
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