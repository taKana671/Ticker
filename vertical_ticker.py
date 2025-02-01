from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, Vec3, CardMaker

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



class VerticalTicker(NodePath):

    def __init__(self):
        super().__init__(PandaNode('vertical_ticker'))
        self.reparent_to(base.render)
        self.set_pos_hpr(Point3(5, 0, -3), Vec3(0, 0, 0))
        self.create_ticker()

    def create_ticker(self):
        # make building
        self.building = NodePath('buildong')
        self.building.reparent_to(self)

        model = BoxModel('building', width=5, depth=5, height=10)
        model.set_texture(base.loader.load_texture('textures/tile_05.jpg'))
        model.reparent_to(self.building)

        frame = BoxModel('frame', width=1, depth=1.5, height=5)
        frame.set_texture(base.loader.load_texture('textures/concrete_01.jpg'))
        frame.set_pos(Point3(-2, -3.25, 2))
        frame.reparent_to(self.building)

        self.ticker = NodePath('ticker')
        card = CardMaker('card')
        card.set_frame(-0.6, 0.6, -2.4, 2.4)
        model = self.ticker.attach_new_node(card.generate())
        model.set_color((0, 0, 0, 1))
        self.ticker.set_pos_hpr(Point3(-0.59, 0, 0.05), Vec3(270, 0, 0))
        self.ticker.reparent_to(frame)

    def update(self, dt):
        pass

