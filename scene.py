import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletConvexHullShape, BulletPlaneShape
from panda3d.core import NodePath
from panda3d.core import Point3, Vec3, BitMask32, LColor
from panda3d.core import AmbientLight, DirectionalLight

from voronoi_generator.voronoi_3d.clip2cube.clip2cube import VoronoiClipped2Cube
from shapes import RandomConvexPolyhedron


class VoronoiCell3D(NodePath):

    def __init__(self, serial, model, pos, color):
        super().__init__(BulletRigidBodyNode(f'voronoi_cell_{serial}'))
        self.model = model
        model.reparent_to(self)
        self.node().deactivation_enabled = True

        shape = BulletConvexHullShape()
        shape.add_geom(model.node().get_geom(0))
        self.node().add_shape(shape)
        self.node().set_mass(1)

        self.set_collide_mask(BitMask32.bit(1))
        self.set_pos(pos)
        self.set_color(color)


class Ground(NodePath):

    def __init__(self, pos):
        super().__init__(BulletRigidBodyNode('ground'))
        shape = BulletPlaneShape(Vec3(0, 0, 1), 0)
        self.node().add_shape(shape)
        self.set_collide_mask(BitMask32.allOn())
        self.node().set_mass(0)
        self.set_pos(pos)


class Scene:

    def __init__(self):
        self.scene = NodePath('scene')
        self.scene.reparent_to(base.render)

        self.ground = Ground(Point3(0, 0, 0))
        self.ground.reparent_to(self.scene)
        base.world.attach(self.ground.node())

        self.cells = NodePath('cells')
        self.cells.reparent_to(self.scene)

    def setup_light(self):
        ambient_light = NodePath(AmbientLight('ambient_light'))
        ambient_light.reparent_to(base.render)
        ambient_light.node().set_color(LColor(0.6, 0.6, 0.6, 1.0))
        base.render.set_light(ambient_light)

        directional_light = NodePath(DirectionalLight('directional_light'))
        directional_light.node().get_lens().set_film_size(200, 200)
        directional_light.node().get_lens().set_near_far(1, 100)
        directional_light.node().set_color(LColor(1, 1, 1, 1))
        directional_light.set_pos_hpr(Point3(0, 0, 50), Vec3(-30, -45, 0))
        # directional_light.node().show_frustom()
        base.render.set_light(directional_light)
        directional_light.node().set_shadow_caster(True)
        base.render.set_shader_auto()

    def create_voronoi_cube(self, config):
        if config['multi_processing']:
            self.clip_multoprocess(**config['clipping'], **config['polyhedron'])
        else:
            self.clip(**config['clipping'], **config['polyhedron'])

    def create_voronoi_cell(self, vertices, serial, cube_size, max_depth, scale):
        model_creator = RandomConvexPolyhedron(vertices, max_depth, scale)
        model = model_creator.create()

        n = scale * cube_size / 2
        pos = Point3(*model_creator.polyhedron_org_center * scale) - Vec3(n, n, 0)
        color = LColor(*np.random.uniform(0, 1, 3), 1)
        voronoi_cell = VoronoiCell3D(serial, model, pos, color)

        return voronoi_cell

    def attach_voronoi_cell(self, voronoi_cell):
        # When changing a static body to a rigid body and applying a force, the `apply_central_force` only worked
        # if assigning a mass greater than 0, attaching it to the world, then set the mass to 0, and finally
        # changed it back to 1 when applying the force.
        voronoi_cell.reparent_to(self.cells)
        base.world.attach(voronoi_cell.node())
        voronoi_cell.node().set_mass(0)

    def clip(self, cut_points, cube_size, diff, max_depth, scale):
        """Clip voronoi cells to cube.
            Args:
                cut_points(int): the number of polyhedrons to divide a cube into.
                cube_size (float): length of a cube's edge.
                diff (float): how far from the vertices of the cube the dummy points should be placed.
                max_depth (int): the number of divisions of one triangle; cannot be negative.
                scale (float): the scale of the polyhedron; greater than 0.
        """
        start = time.perf_counter()

        for serial, vertices in enumerate(VoronoiClipped2Cube(cut_points, cube_size, diff)):
            voronoi_cell = self.create_voronoi_cell(vertices, serial, cube_size, max_depth, scale)
            self.attach_voronoi_cell(voronoi_cell)

        print(f'Took {time.perf_counter() - start}')

    def clip_multoprocess(self, cut_points, cube_size, diff, max_depth, scale):
        start = time.perf_counter()

        with ProcessPoolExecutor() as executor:
            results = [executor.submit(self.create_voronoi_cell, vertices, serial, cube_size, max_depth, scale)
                       for serial, vertices in enumerate(VoronoiClipped2Cube(cut_points, cube_size, diff))]

        for result in results:
            voronoi_cell = result.result()
            self.attach_voronoi_cell(voronoi_cell)

        print(f'Took {time.perf_counter() - start}')

    def set_mass_to_cells(self):
        for voroni_cell in self.cells.get_children():
            voroni_cell.node().deactivation_enabled = False
            voroni_cell.node().set_mass(1)

    def apply_force(self):
        for voronoi_cell in self.cells.get_children():
            voronoi_cell.node().apply_central_force(Vec3.up() * 10)