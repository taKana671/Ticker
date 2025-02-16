from panda3d.core import AmbientLight, Spotlight
from panda3d.core import NodePath
from panda3d.core import Vec3, Point3, LColor


class BasicAmbientLight(NodePath):

    def __init__(self):
        super().__init__(AmbientLight('ambient_light'))
        base.render.set_light(self)
        self.reparent_to(base.render)
        self.node().set_color(LColor(0.9, 0.9, 0.9, 1))


class BasicSpotlight(NodePath):

    def __init__(self, fov=60, near=0.5, far=5, debug=False):
        super().__init__(Spotlight('spotlight'))
        # self.reparent_to(base.render)
        self.node().set_color(LColor(1, 1, 1, 1))
        self.node().set_attenuation(Vec3(0, 0, 0.001))
        self.node().set_exponent(20)
        self.node().get_lens().set_fov(fov)
        self.node().get_lens().set_near_far(near, far)
        self.node().set_shadow_caster(True)

        if debug:
            self.node().show_frustum()

    def setup_light(self, np):
        np.set_light(self)
        np.set_shader_auto()