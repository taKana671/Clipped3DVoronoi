import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import numpy as np
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletTriangleMeshShape, BulletTriangleMesh
from panda3d.bullet import BulletConvexHullShape, BulletPlaneShape, BulletCylinderShape, ZUp
from panda3d.core import NodePath, PandaNode
from panda3d.core import Point3, Vec3, BitMask32, LColor
from panda3d.core import TextureStage, TransformState, TexGenAttrib
from panda3d.core import AmbientLight, DirectionalLight

from voronoi_generator.voronoi_3d.clip2cube.visualize import visualize
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

    def create_voronoi_cells2(self):
        start = time.perf_counter()
        scale = 2  # scaleを1にしてcube_sizeを上げ、creator.polyhedron_org_centerにscaleをかけない。

        for i, clipped_vertices in enumerate(VoronoiClipped2Cube(cut_points=30)):

            model_creator = RandomConvexPolyhedron(clipped_vertices, max_depth=2, scale=scale)
            model = model_creator.create()

            color = LColor(*np.random.uniform(0, 1, 3), 1)
            diff = Vec3(scale / 2, scale / 2, 0)
            pos = Point3(*model_creator.polyhedron_org_center * scale) - diff
            voronoi_cell = VoronoiCell3D(i, model, pos, color)
            voronoi_cell.reparent_to(self.cells)

            # When changing a static body to a rigid body and applying a force, the `apply_central_force` function only worked
            # if assigning a mass greater than 0, attaching it to the world, then set the mass to 0, and finally changed it back to 1 
            # when applying the force.
            base.world.attach(voronoi_cell.node())
            voronoi_cell.node().set_mass(0)

        print(f'Took {time.perf_counter() - start}')


    def create_cell(self, clipped_vertices, scale, i):
        model_creator = RandomConvexPolyhedron(clipped_vertices, max_depth=2, scale=scale)
        model = model_creator.create()

        color = LColor(*np.random.uniform(0, 1, 3), 1)
        diff = Vec3(scale / 2, scale / 2, 0)
        pos = Point3(*model_creator.polyhedron_org_center * scale) - diff
        voronoi_cell = VoronoiCell3D(i, model, pos, color)
        # voronoi_cell.reparent_to(self.cells)

        # When changing a static body to a rigid body and applying a force, the `apply_central_force` function only worked
        # if assigning a mass greater than 0, attaching it to the world, then set the mass to 0, and finally changed it back to 1 
        # when applying the force.
        # base.world.attach(voronoi_cell.node())
        # voronoi_cell.node().set_mass(0)

        return voronoi_cell


    def create_voronoi_cells(self):
        start = time.perf_counter()
        scale = 2  # scaleを1にしてcube_sizeを上げ、creator.polyhedron_org_centerにscaleをかけない。
        results = []

        with ProcessPoolExecutor() as executor:
            for i, clipped_vertices in enumerate(VoronoiClipped2Cube(cut_points=30)):
                results.append(executor.submit(self.create_cell, clipped_vertices, scale, i))

                # model_creator = RandomConvexPolyhedron(clipped_vertices, max_depth=3, scale=scale)
                # model = model_creator.create()

                # color = LColor(*np.random.uniform(0, 1, 3), 1)
                # diff = Vec3(scale / 2, scale / 2, 0)
                # pos = Point3(*model_creator.polyhedron_org_center * scale) - diff
                # voronoi_cell = VoronoiCell3D(i, model, pos, color)
                # voronoi_cell.reparent_to(self.cells)

                # # When changing a static body to a rigid body and applying a force, the `apply_central_force` function only worked
                # # if assigning a mass greater than 0, attaching it to the world, then set the mass to 0, and finally changed it back to 1 
                # # when applying the force.
                # base.world.attach(voronoi_cell.node())
                # voronoi_cell.node().set_mass(0)

        for result in results:
            # model, center = result.result()
            # color = LColor(*np.random.uniform(0, 1, 3), 1)
            # diff = Vec3(scale / 2, scale / 2, 0)
            # pos = Point3(*center * scale) - diff
            # voronoi_cell = VoronoiCell3D(i, model, pos, color)

            voronoi_cell = result.result()
            voronoi_cell.reparent_to(self.cells)

            # When changing a static body to a rigid body and applying a force, the `apply_central_force` function only worked
            # if assigning a mass greater than 0, attaching it to the world, then set the mass to 0, and finally changed it back to 1 
            # when applying the force.
            base.world.attach(voronoi_cell.node())
            voronoi_cell.node().set_mass(0)



        print(f'Took {time.perf_counter() - start}')
        # import pdb; pdb.set_trace()

    def set_mass_to_cells(self):
        for voroni_cell in self.cells.get_children():
            voroni_cell.node().deactivation_enabled = False
            voroni_cell.node().set_mass(1)

    def apply_force(self):
        for voronoi_cell in self.cells.get_children():
            voronoi_cell.node().apply_central_force(Vec3.up() * 10)


        

# def create_cell(clipped_vertices, scale, i):
#     model_creator = RandomConvexPolyhedron(clipped_vertices, max_depth=3, scale=scale)
#     model = model_creator.create()

#     color = LColor(*np.random.uniform(0, 1, 3), 1)
#     diff = Vec3(scale / 2, scale / 2, 0)
#     pos = Point3(*model_creator.polyhedron_org_center * scale) - diff
#     voronoi_cell = VoronoiCell3D(i, model, pos, color)

#     return voronoi_cell
    # return model, model_creator.polyhedron_org_center