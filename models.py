from panda3d.core import NodePath, PandaNode

from shapes.src import Box, Cylinder


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


class CylinderModel(NodePath):

    def __init__(self, name, radius, inner_radius=0, height=1, segs_top_cap=0, segs_bottom_cap=0):
        super().__init__(PandaNode(name))
        self.model = Cylinder(
            radius=radius,
            inner_radius=inner_radius,
            height=height,
            segs_top_cap=segs_top_cap,
            segs_bottom_cap=segs_bottom_cap).create()

        self.model.reparent_to(self)