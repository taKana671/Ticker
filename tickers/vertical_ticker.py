from panda3d.core import NodePath
from panda3d.core import Point3, Vec3, CardMaker
# from direct.interval.LerpInterval import LerpTexOffsetInterval

from .base_ticker import Process, Size, BaseTicker
from .ticker_displays import VerticalDisplay
from .models import BoxModel


class VerticalTicker(BaseTicker):

    def __init__(self, parent, msg, pos, hpr):
        super().__init__('vertical_ticker', parent, pos, hpr)
        self.next_msg = None
        self.process = None
        self.counter = 0
        self.create_ticker(msg)

    def create_ticker(self, msg):
        self.building = NodePath('buildong')
        self.building.reparent_to(self.root)

        model = BoxModel('building', width=5, depth=5, height=10)
        model.set_texture(base.loader.load_texture('textures/tile_05.jpg'))
        model.reparent_to(self.building)

        frame = BoxModel('frame', width=1, depth=1.2, height=5)
        frame.set_texture(base.loader.load_texture('textures/concrete_01.jpg'))
        frame.set_pos(Point3(-2, -3.1, 2))
        frame.reparent_to(self.building)

        ticker = NodePath('ticker')
        model = BoxModel('ticker_display', width=1.2, depth=4.8, height=1, open_top=True, open_bottom=True)
        model.reparent_to(ticker)
        ticker.set_pos_hpr(Point3(0, 0, 0), Vec3(0, 90, 0))   # Point3(-0.45, 0, 0.0)
        ticker.reparent_to(frame)

        size = Size(256 * 10, 256 * 2, 3)
        self.ticker = VerticalDisplay(model, size, msg)
        # LerpTexOffsetInterval(model, 5, (1, 0), (0, 0)).loop()

    def change_message(self, msg):
        self.ticker.prepare_for_deletion()
        self.process = Process.DELETE
        self.next_msg = msg

    def prepare_new_msg(self):
        self.ticker.prepare_for_display(self.next_msg)
        self.next_msg = None

    def delete_old_msg(self):
        if (ret := self.ticker.delete_msg(self.counter)) == 0:
            self.counter = ret
            return True

        self.counter += ret

    def display_new_msg(self):
        if (ret := self.ticker.display_msg(self.counter)) == 0:
            self.counter = ret
            return True

        self.counter += ret

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
