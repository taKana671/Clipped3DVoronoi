import sys
from enum import Enum, auto

import yaml
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.core import Point3, Vec3, Vec2
from panda3d.core import NodePath
from panda3d.core import AntialiasAttrib
from panda3d.core import load_prc_file_data

from scene import Scene


load_prc_file_data("", """
    textures-power-2 none
    gl-coordinate-system default
    window-title Panda3D Voronoi City
    filled-wireframe-apply-shader true
    stm-max-views 8
    stm-max-chunk-count 2048
    framebuffer-multisample 1
    multisamples 2""")


class Status(Enum):

    SET_MASS = auto()
    COLLAPSE = auto()


class ClippedVoronoi(ShowBase):

    def __init__(self, clipping_config):
        super().__init__()
        self.disable_mouse()
        self.render.set_antialias(AntialiasAttrib.MAuto)

        self.world = BulletWorld()
        self.world.set_gravity(Vec3(0, 0, -9.81))
        self.debug = self.render.attach_new_node(BulletDebugNode('debug'))
        self.world.set_debug_node(self.debug.node())

        self.camera_root = NodePath('camera_root')
        self.camera_root.reparent_to(self.render)
        self.camera.reparent_to(self.camera_root)
        self.camera.set_pos(Point3(0, -10, 10))
        self.camera.look_at(Point3(0, 0, 0))

        self.scene = Scene()
        self.scene.create_voronoi_cube(clipping_config)
        self.scene.setup_light()

        self.clicked = False
        self.dragging = False
        self.before_mouse_pos = None
        self.status = None
        self.force = False

        self.accept('escape', sys.exit)
        self.accept('mouse1', self.mouse_click)
        self.accept('mouse1-up', self.mouse_release)
        self.accept('d', self.toggle_debug)
        self.accept('w', self.toggle_wireframe)
        self.accept('u', self.apply_force)

        self.taskMgr.add(self.update, 'update')

    def apply_force(self):
        self.status = Status.SET_MASS

    def toggle_debug(self):
        if self.debug.is_hidden():
            self.debug.show()
        else:
            self.debug.hide()

    def mouse_click(self):
        self.dragging = True
        self.dragging_start_time = globalClock.get_frame_time()

    def mouse_release(self):
        if globalClock.get_frame_time() - self.dragging_start_time < 0.2:
            self.clicked = True

        self.dragging = False
        self.before_mouse_pos = None

    def rotate_camera(self, mouse_pos, dt):
        if self.before_mouse_pos:
            angle = Vec3()

            if (delta := mouse_pos.x - self.before_mouse_pos.x) < 0:
                angle.x += 180
            elif delta > 0:
                angle.x -= 180

            if (delta := mouse_pos.y - self.before_mouse_pos.y) < 0:
                angle.z -= 180
            elif delta > 0:
                angle.z += 180

            angle *= dt
            self.camera_root.set_hpr(self.camera_root.get_hpr() + angle)

        self.before_mouse_pos = Vec2(mouse_pos.xy)

    def update(self, task):
        dt = globalClock.get_dt()

        match self.status:

            case Status.SET_MASS:
                self.scene.set_mass_to_cells()
                self.status = Status.COLLAPSE

            case Status.COLLAPSE:
                self.scene.apply_force()
                self.status = None

        if self.mouseWatcherNode.has_mouse():
            mouse_pos = self.mouseWatcherNode.get_mouse()

            if self.dragging:
                if globalClock.get_frame_time() - self.dragging_start_time >= 0.2:
                    self.rotate_camera(mouse_pos, dt)

        self.world.do_physics(dt)
        return task.cont


def main():
    with open('clipping_config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    app = ClippedVoronoi(config)
    app.run()


if __name__ == '__main__':
    main()