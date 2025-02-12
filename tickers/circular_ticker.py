from panda3d.core import NodePath
from panda3d.core import Point3, Vec3, LColor

from .base_ticker import Process, Size, BaseTicker
from .ticker_displays import CircularDisplay
from .models import CylinderModel


class CircularTicker(BaseTicker):

    def __init__(self, msg):
        super().__init__('circular_ticker')
        self.process = None
        self.counter = 0
        self.create_ticker(msg)

    def create_ticker(self, msg):
        self.ticker_display = NodePath("ticker_display")
        self.ticker_display.reparent_to(self.root)

        framework = NodePath('framework')
        framework.set_texture(base.loader.load_texture('textures/concrete_01.jpg'))
        framework.reparent_to(self.ticker_display)

        rad = 4.48
        inner_rad = 4.08

        model = CylinderModel(
            'frame', radius=rad, inner_radius=inner_rad, height=1, segs_bottom_cap=3, segs_top_cap=3)
        model.reparent_to(framework)

        pole_rad = (rad - inner_rad) / 2
        v = rad - pole_rad
        xy = [(0, -v), (0, v), (-v, 0), (v, 0)]

        for i, (x, y) in enumerate(xy):
            model = CylinderModel(
                f'pole_{i}', radius=pole_rad, height=6, segs_bottom_cap=2, segs_top_cap=2)
            model.set_pos_hpr(Point3(x, y, 0), Vec3(0, 180, 0))
            model.reparent_to(framework)

        ticker = NodePath('ticker')
        size = Size(256 * 20, 256 * 2, 3)
        self.tickers = []

        for i, (rad, is_outer) in enumerate([[4.0, False], [4.5, True]]):
            model = CylinderModel(f'ticker_{i}', radius=rad, height=1)
            model.reparent_to(ticker)
            display = CircularDisplay(model, size, msg, outer=is_outer)
            self.tickers.append(display)

        ticker.reparent_to(self.ticker_display)

    def change_message(self, msg):
        self.process = Process.DELETE
        self.next_msg = msg

    def delete_old_msg(self):
        if all([t.delete_msg(self.counter) for t in self.tickers]):
            self.counter = 0
            return True

        self.counter += 1

    def prepare_new_msg(self):
        for t in self.tickers:
            t.prepare_for_display(self.next_msg)

        self.next_msg = None

    def display_new_msg(self):
        if all([t.display_msg(self.counter) for t in self.tickers]):
            self.counter = 0
            return True

        self.counter += 1

    def rotate_display(self, dt):
        for t in self.tickers:
            t.move_letters(dt)

    def update(self, dt):
        self.rotate_display(dt)

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