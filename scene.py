from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletConvexHullShape, BulletPlaneShape
from panda3d.core import NodePath
from panda3d.core import BitMask32, Point3, Vec3, LColor

from shapes import RandomConvexPolyhedron, ShatteredSphere
from utils import clock
from voronoi_generator.voronoi_3d.clip2cube import VoronoiClip2Cube
from voronoi_generator.voronoi_3d.clip2sphere import VoronoiClip2Sphere


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


class Scene(ABC):

    def __init__(self):
        self.scene = NodePath('scene')
        self.scene.reparent_to(base.render)

        self.ground = Ground(Point3(0, 0, 0))
        self.ground.reparent_to(self.scene)
        base.world.attach(self.ground.node())

        self.cells = NodePath('cells')
        self.cells.reparent_to(self.scene)

    @abstractmethod
    def clip(self, **kwargs):
        """Clip to the specified shape."""

    @abstractmethod
    def clip_multiprocess(self, **kwargs):
        """Clip to the specified shape in multiprocess."""

    def create_voronoi_cells(self, config):
        kwargs = {k: v for k, v in config.items() if k != 'multi_processing'}

        if config['multi_processing']:
            self.clip_multiprocess(**kwargs)
        else:
            self.clip(**kwargs)

    def attach_voronoi_cell(self, voronoi_cell):
        # When changing a static body to a rigid body and applying a force, the `apply_central_force` only worked
        # if assigning a mass greater than 0, attaching it to the world, then set the mass to 0, and finally
        # changed it back to 1 when applying the force.
        voronoi_cell.reparent_to(self.cells)
        base.world.attach(voronoi_cell.node())
        voronoi_cell.node().set_mass(0)

    def create_voronoi_model(self, model_creator, serial, scale, offset):
        model = model_creator.create()
        pos = Point3(*model_creator.polyhedron_org_center * scale) + offset * scale
        color = LColor(*np.random.uniform(0, 1, 3), 1)
        voronoi_cell = VoronoiCell3D(serial, model, pos, color)

        return voronoi_cell

    def set_mass_to_cells(self):
        for voroni_cell in self.cells.get_children():
            voroni_cell.node().deactivation_enabled = False
            voroni_cell.node().set_mass(1)

    def apply_force(self):
        for voronoi_cell in self.cells.get_children():
            voronoi_cell.node().apply_central_force(Vec3.up() * 10)


class ClippingMixin:

    def get_future_result(self, futures):
        for future in as_completed(futures):
            voronoi_cell = future.result()
            self.attach_voronoi_cell(voronoi_cell)


class SphereClipping(ClippingMixin, Scene):

    @clock()
    def clip(self, cut_points, max_depth, scale):
        """Clip voronoi cells to cube.
            Args:
                cut_points(int): the number of polyhedrons to divide a cube into.
                max_depth (int): the number of divisions of one triangle; cannot be negative.
                scale (float): the scale of the polyhedron; greater than 0.
        """
        for i, (polygons, spherical_idx) in enumerate(VoronoiClip2Sphere(cut_points)):
            voronoi_cell = self.create_voronoi_cell(i, polygons, spherical_idx, max_depth, scale)
            self.attach_voronoi_cell(voronoi_cell)

    @clock()
    def clip_multiprocess(self, cut_points, max_depth, scale):
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(self.create_voronoi_cell, i, polygons, spherical_idx, max_depth, scale)
                       for i, (polygons, spherical_idx) in enumerate(VoronoiClip2Sphere(cut_points))]

        self.get_future_result(futures)

    def create_voronoi_cell(self, serial, polygons, spherical_idx, max_depth, scale):
        model_creator = ShatteredSphere(polygons, spherical_idx, max_depth, scale)
        voronoi_cell = self.create_voronoi_model(model_creator, serial, scale, Vec3(0, 0, 1))

        return voronoi_cell


class CubeClipping(ClippingMixin, Scene):

    @clock()
    def clip(self, cut_points, cube_size, diff, max_depth, scale):
        """Clip voronoi cells to cube.
            Args:
                cut_points(int): the number of polyhedrons to divide a cube into.
                cube_size (float): length of a cube's edge.
                diff (float): how far from the vertices of the cube the dummy points should be placed.
                max_depth (int): the number of divisions of one triangle; cannot be negative.
                scale (float): the scale of the polyhedron; greater than 0.
        """
        for i, polygons in enumerate(VoronoiClip2Cube(cut_points, cube_size, diff)):
            voronoi_cell = self.create_voronoi_cell(i, polygons, max_depth, cube_size, scale)
            self.attach_voronoi_cell(voronoi_cell)

    @clock()
    def clip_multiprocess(self, cut_points, cube_size, diff, max_depth, scale):
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(self.create_voronoi_cell, i, polygons, max_depth, cube_size, scale)
                       for i, polygons in enumerate(VoronoiClip2Cube(cut_points, cube_size, diff))]

        self.get_future_result(futures)

    def create_voronoi_cell(self, serial, polygons, max_depth, cube_size, scale):
        model_creator = RandomConvexPolyhedron(polygons, max_depth, scale)
        voronoi_cell = self.create_voronoi_model(model_creator, serial, scale, Vec3(0, 0, cube_size * 0.5))

        return voronoi_cell