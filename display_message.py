import sys
import math

from panda3d.core import Texture, TextureStage, TransformState
from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, PandaNode, TextNode
from panda3d.core import Point3, Vec3, PTA_uchar, CPTA_uchar, LColor, Vec4
from panda3d.core import OrthographicLens, Camera, MouseWatcher, PGTop
from panda3d.core import Shader, TextureStage, TransparencyAttrib
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectEntry
from direct.showbase.ShowBaseGlobal import globalClock

from ticker import CircularTicker


class DisplayMessage(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()

        # self.camera.set_pos(-10, -5, 3)
        # self.camera.reparent_to(self.render)

        self.display_root = NodePath('camera_root')
        self.display_root.reparent_to(self.render)

        self.ticker = CircularTicker()
        self.ticker.reparent_to(self.display_root)

        self.create_display_region()
        self.create_gui_region()
        self.gui = Gui()

        self.color_change = False
        # self.camera.look_at(self.ticker.outer.model)
        self.camera.look_at(Point3(0, 0, 0))

        self.accept('d', self.start_change)
        self.accept('escape', sys.exit)
        self.taskMgr.add(self.update, 'update')

    def calc_aspect_ratio(self, display_region):
        """Args:
            display_region (Vec4): (left, right, bottom, top)
            The range is from 0 to 1.
            0: the left and bottom; 1: the right and top.
        """
        props = self.win.get_properties()
        window_size = props.get_size()

        region_w = display_region.y - display_region.x
        region_h = display_region.w - display_region.z
        display_w = int(window_size.x * region_w)
        display_h = int(window_size.y * region_h)

        gcd = math.gcd(display_w, display_h)
        w = display_w / gcd
        h = display_h / gcd
        aspect_ratio = w / h

        return aspect_ratio

    def calc_scale(self, region_size):
        aspect_ratio = self.get_aspect_ratio()

        w = region_size.y - region_size.x
        h = region_size.w - region_size.z
        new_aspect_ratio = aspect_ratio * w / h

        if aspect_ratio > 1.0:
            s = 1. / h
            return Vec3(s / new_aspect_ratio, 1.0, s)
        else:
            s = 1.0 / w
            return Vec3(s, 1.0, s * new_aspect_ratio)

    def create_gui_region(self):
        """Create the custom 2D region for slider and label.
        """
        # (left, right, bottom, top)
        region_size = Vec4(0.0, 1.0, 0.0, 0.1)
        region = self.win.make_display_region(region_size)
        region.set_sort(20)
        region.set_clear_color((0.5, 0.5, 0.5, 1.0))
        region.set_clear_color_active(True)

        gui_cam = NodePath(Camera('cam2d'))
        lens = OrthographicLens()
        lens.set_film_size(2, 2)
        lens.set_near_far(-1000, 1000)
        gui_cam.node().set_lens(lens)

        gui_render2d = NodePath('gui_render2d')
        gui_render2d.set_depth_test(False)
        gui_render2d.set_depth_write(False)
        gui_cam.reparent_to(gui_render2d)
        region.set_camera(gui_cam)

        self.gui_aspect2d = gui_render2d.attach_new_node(PGTop('gui_aspect2d'))
        scale = self.calc_scale(region_size)
        self.gui_aspect2d.set_scale(scale)

        mw2d_node = self.create_mouse_watcher('mw2d', region)
        self.gui_aspect2d.node().set_mouse_watcher(mw2d_node)

    def create_display_region(self):
        """Create the region to display terrain.
        """
        # (left, right, bottom, top)
        region_size = Vec4(0.0, 1.0, 0.1, 1.0)
        region = self.win.make_display_region(region_size)

        self.display_cam = NodePath(Camera('cam3d'))
        aspect_ratio = self.calc_aspect_ratio(region_size)
        self.display_cam.node().get_lens().set_aspect_ratio(aspect_ratio)
        self.display_cam.node().get_lens().set_fov(60)
        region.set_camera(self.display_cam)
        self.camNode.set_active(False)

        # self.display_cam.set_pos(-10, -5, 3)
        self.display_cam.set_pos(-10, -10, 3)
        # self.display_cam.set_pos(Point3(0, self.img_size.y * -1, 200))
        self.display_cam.look_at(Point3(0, 0, 0))
        self.display_cam.reparent_to(self.display_root)
        self.display_mw = self.create_mouse_watcher('mw3d', region)

    def create_mouse_watcher(self, name, display_region):
        mw_node = MouseWatcher(name)
        input_ctrl = self.mouseWatcher.get_parent()
        input_ctrl.attach_new_node(mw_node)
        mw_node.set_display_region(display_region)
        return mw_node

    def start_change(self):
        print('called!')
        self.color_change = True

    def update(self, task):
        dt = globalClock.get_dt()
        self.ticker.update(dt)

        if self.gui.entered_text:
            self.ticker.change_message(self.gui.entered_text)
            self.gui.entered_text = ''

        return task.cont


class Gui(DirectFrame):

    def __init__(self):
        super().__init__(
            parent=base.gui_aspect2d,
            frameColor=(.5, .5, .5, 0),
            frameSize=(-1, 1, -1, 1),
            pos=Point3(0, 0, 0)
        )
        self.initialiseoptions(type(self))
        self.set_transparency(TransparencyAttrib.MAlpha)
        self.create_widget()
        self.entered_text = ''

    def create_widget(self):
        DirectLabel(
            parent=self,
            pos=Point3(-1., 0., -0.01),
            frameColor=(1, 1, 1, 0),
            text_scale=0.06,
            text_fg=(1, 1, 1, 1),
            text='message',
            text_align=TextNode.ARight,
        )
        self.entry = DirectEntry(
            parent=self,
            pos=(-0.95, 0., -0.02),
            scale=0.07,
            width=30,
            command=self.set_entered_text
        )

    def set_entered_text(self, entered_text):
        if entered_text:
            self.entered_text = entered_text
            print(self.entered_text)






if __name__ == '__main__':
    ticker = DisplayMessage()
    ticker.run()