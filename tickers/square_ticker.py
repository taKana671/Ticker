from panda3d.core import NodePath
from panda3d.core import Point3, Vec3, LColor, CardMaker
# from direct.interval.LerpInterval import LerpTexOffsetInterval

from .base_ticker import Process, Size, BaseTicker
from .ticker_displays import SquareDisplay
from .models import BoxModel, LampShade
from lights import BasicSpotlight



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

        # make lampshades an lights
        # If the spot_light is parented to the lamp_shape, it's put in world coords position.
        # To prevent this, the spot_light needs to be parented to the self.building.
        # Or after VerticalTiker class is instanced, parent spot_lignt to base.render and position it
        # like spot_light.set_pos_hpr(lamp_shade, Point3(0, 0, 0), Vec3(0, 0, 0))
        lamp_shades = [
            [Point3(-5.2, -2.3, 4.8), Vec3(0, -60, 0)],
            [Point3(-5.2, 2.3, 4.8), Vec3(0, -120, 0)]
        ]
        for pos, hpr in lamp_shades:
            lamp_shade = LampShade('lamp_shade1')
            lamp_shade.set_pos_hpr(pos, hpr)
            lamp_shade.reparent_to(self.building)

        lights = [
            [Point3(-9, -3.5, 5.5), Vec3(-60, -30, 0)],
            [Point3(-9, 3.5, 5.5), Vec3(-120, -30, 0)]
        ]
        for pos, hpr in lights:
            spot_light = BasicSpotlight(LColor(1, 1, 0, 1), fov=30, far=3)
            spot_light.reparent_to(self.building)
            spot_light.set_pos_hpr(pos, hpr)
            spot_light.setup_light(board)

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