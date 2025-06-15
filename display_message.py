import sys
import math

import direct.gui.DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectEntry, DirectFrame, DirectLabel, DirectButton
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import NodePath, TextNode
from panda3d.core import Point3, Vec3, LColor, Vec4
from panda3d.core import OrthographicLens, Camera, MouseWatcher, PGTop
from panda3d.core import TransparencyAttrib, AntialiasAttrib, TexGenAttrib
from panda3d.core import load_prc_file_data
from panda3d.core import TextureStage

from lights import BasicAmbientLight
from tickers.circular_ticker import CircularTicker
from tickers.square_ticker import SquareTicker
from tickers.vertical_ticker import VerticalTicker
from shapes import Sphere

load_prc_file_data("", """
    framebuffer-multisample 1
    multisamples 2
""")


class DisplayMessage(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        self.render.set_antialias(AntialiasAttrib.MAuto)

        self.create_3d_region()
        self.create_2d_region()
        self.create_tickers()
        self.create_sky()
        self.gui = Gui()

        self.ambient_light = BasicAmbientLight()

        self.accept('escape', sys.exit)
        self.taskMgr.add(self.update, 'update')

    def create_tickers(self):
        self.scene = NodePath('scene')
        self.scene.reparent_to(self.render)
        self.tickers = {}

        c_ticker = CircularTicker('Enjoy 3D programming.')
        c_ticker.set_pos_hpr(Point3(-2.5, -1, 1), Vec3(0, 0, 0))
        c_ticker.reparent_to(self.render)
        self.tickers['c'] = c_ticker

        s_ticker = SquareTicker('Panda3D')
        s_ticker.set_pos_hpr(Point3(2, 10, 1), Vec3(90, 0, 0))
        s_ticker.reparent_to(self.render)
        self.tickers['s'] = s_ticker

        v_ticker = VerticalTicker('Welcome')
        v_ticker.set_pos_hpr(Point3(8.5, 2.5, 0), Vec3(35, 0, 0))
        v_ticker.reparent_to(self.render)
        self.tickers['v'] = v_ticker

    def create_sky(self):
        np = NodePath('skybox')
        np.reparent_to(self.render)
        sphere = Sphere(radius=500).create()
        sphere.set_pos(Point3(45, 0, -350))
        sphere.reparent_to(np)

        ts = TextureStage.get_default()
        sphere.set_tex_gen(ts, TexGenAttrib.M_world_cube_map)
        sphere.set_tex_hpr(ts, (0, 180, 0))
        sphere.set_tex_scale(ts, (1, -1))

        sphere.set_light_off()
        sphere.set_material_off()
        imgs = base.loader.load_cube_map('textures/skybox/img_#.png')
        sphere.set_texture(imgs)

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

    def create_2d_region(self):
        """Create the custom 2D region for gui.
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

    def create_3d_region(self):
        """Create the region for tickers.
        """
        # (left, right, bottom, top)
        region_size = Vec4(0.0, 1.0, 0.1, 1.0)
        region = self.win.make_display_region(region_size)

        self.cam3d = NodePath(Camera('cam3d'))
        aspect_ratio = self.calc_aspect_ratio(region_size)
        self.cam3d.node().get_lens().set_aspect_ratio(aspect_ratio)
        region.set_camera(self.cam3d)
        self.camNode.set_active(False)

        self.cam3d.set_pos_hpr(Point3(-14.5, -12, 5), Vec3(-46.565052, -4.648583, 0))
        self.cam3d.reparent_to(self.render)
        self.display_mw = self.create_mouse_watcher('mw3d', region)

    def create_mouse_watcher(self, name, display_region):
        mw_node = MouseWatcher(name)
        input_ctrl = self.mouseWatcher.get_parent()
        input_ctrl.attach_new_node(mw_node)
        mw_node.set_display_region(display_region)
        return mw_node

    def update(self, task):
        dt = globalClock.get_dt()
        for ticker in self.tickers.values():
            ticker.update(dt)

        return task.cont


class Gui(DirectFrame):

    def __init__(self):
        super().__init__(
            parent=base.gui_aspect2d,
            frameColor=(.6, .6, .6, 0),
            frameSize=(-1, 1, -1, 1),
            pos=Point3(0, 0, 0)
        )

        self.initialiseoptions(type(self))
        self.set_transparency(TransparencyAttrib.MAlpha)
        self.create_widget()

    def create_widget(self):
        text_fg = LColor(1, 1, 1, 1)
        text_scale = 0.06
        frame_color = LColor(0.6, 0.6, 0.6, 1)

        DirectLabel(
            parent=self,
            pos=Point3(-1., 0., -0.01),
            frameColor=(1, 1, 1, 0),
            text_scale=text_scale,
            text_fg=text_fg,
            text='message',
            text_align=TextNode.ARight,
        )

        self.entry = DirectEntry(
            parent=self,
            pos=(-0.95, 0., -0.02),
            scale=0.07,
            width=23,
            frameColor=frame_color,
            relief=DGG.SUNKEN,
            numLines=1
        )

        start_x = 0.9
        for i, text in enumerate(base.tickers.keys()):
            x = start_x + i * 0.12

            DirectButton(
                parent=self,
                pressEffect=1,
                relief=DGG.RAISED,
                pos=Point3(x, 0, 0),
                text=text,
                frameSize=(-0.06, 0.06, -0.06, 0.06),
                frameColor=frame_color,
                borderWidth=(0.01, 0.01),
                text_scale=text_scale,
                text_pos=(0, -0.01),
                text_fg=text_fg,
                command=self.change_message,
                extraArgs=[text]
            )

    def change_message(self, btn_type):
        if (msg := self.entry.get()).strip():
            ticker = base.tickers[btn_type]
            ticker.change_message(msg)
            self.entry.set('')


if __name__ == '__main__':
    ticker = DisplayMessage()
    ticker.run()