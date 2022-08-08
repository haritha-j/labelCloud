import logging
from typing import List, Tuple

import numpy as np
import OpenGL.GL as GL

from ..control.config_manager import config
from ..definitions import BBOX_EDGES, BBOX_SIDES
from ..utils import math3d, oglhelper


class BBox(object):

    MIN_DIMENSION = config.getfloat("LABEL", "MIN_BOUNDINGBOX_DIMENSION")

    def __init__(
        self,
        cx: float,
        cy: float,
        cz: float,
        length: float = None,
        width: float = None,
        height: float = None,
    ) -> None:
        self.center = cx, cy, cz
        self.length = length or config.getfloat("LABEL", "STD_BOUNDINGBOX_LENGTH")
        self.width = width or config.getfloat("LABEL", "STD_BOUNDINGBOX_WIDTH")
        self.height = height or config.getfloat("LABEL", "STD_BOUNDINGBOX_HEIGHT")
        self.x_rotation = 0
        self.y_rotation = 0
        self.z_rotation = 0
        self.classname = config.get("LABEL", "STD_OBJECT_CLASS")
        self.verticies = None
        self.set_axis_aligned_verticies()


    def sq_distance(self, x1, y1, z1, x2, y2, z2):
        return ((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)

    # GETTERS

    def get_center(self) -> Tuple[float, float, float]:
        return self.center

    def get_dimensions(self) -> Tuple[float, float, float]:
        return self.length, self.width, self.height

    def get_rotations(self) -> Tuple[float, float, float]:
        return self.x_rotation, self.y_rotation, self.z_rotation

    def get_x_rotation(self) -> float:
        return self.x_rotation

    def get_y_rotation(self) -> float:
        return self.y_rotation

    def get_z_rotation(self) -> float:
        return self.z_rotation

    def get_classname(self) -> str:
        return self.classname

    def get_vertices(self) -> np.array:
        rotated_vertices = math3d.rotate_bbox_around_center(
            self.get_axis_aligned_vertices(),
            list(self.center),
            list(self.get_rotations()),
        )
        return np.array(rotated_vertices)

    def get_axis_aligned_vertices(self) -> List[List[float]]:
        coords = []
        for vertex in self.verticies:  # Translate relative bbox to center
            coords.append(math3d.translate_point(vertex, *self.center))
        return coords

    def get_volume(self) -> float:
        return self.length * self.width * self.height

    # SETTERS

    def set_classname(self, classname) -> None:
        if classname:
            self.classname = classname

    def set_length(self, length) -> None:
        if length > 0:
            self.length = length
        else:
            logging.warning("New length is too small.")

    def set_width(self, width) -> None:
        if width > 0:
            self.width = width
        else:
            logging.warning("New width is too small.")

    def set_height(self, height) -> None:
        if height > 0:
            self.height = height
        else:
            logging.warning("New height is too small.")

    def set_dimensions(self, length, width, height) -> None:
        if (length > 0) and (width > 0) and (height > 0):
            self.length = length
            self.width = width
            self.height = height
        else:
            logging.warning("New dimensions are too small.")

    def set_x_rotation(self, angle) -> None:
        self.x_rotation = angle % 360

    def set_y_rotation(self, angle) -> None:
        self.y_rotation = angle % 360

    def set_z_rotation(self, angle) -> None:
        self.z_rotation = angle % 360

    def set_rotations(self, x_angle, y_angle, z_angle):
        self.x_rotation = x_angle
        self.y_rotation = y_angle
        self.z_rotation = z_angle

    def set_x_translation(self, x_translation) -> None:
        self.center = (x_translation, *self.center[1:])

    def set_y_translation(self, y_translation) -> None:
        self.center = (self.center[0], y_translation, self.center[2])

    def set_z_translation(self, z_translation) -> None:
        self.center = (*self.center[:2], z_translation)

    # Updates the dimension of the BBox (important after scaling!)
    def set_axis_aligned_verticies(self) -> None:
        self.verticies = np.array(
            [
                [-self.length / 2, -self.width / 2, -self.height / 2],
                [-self.length / 2, self.width / 2, -self.height / 2],
                [self.length / 2, self.width / 2, -self.height / 2],
                [self.length / 2, -self.width / 2, -self.height / 2],
                [-self.length / 2, -self.width / 2, self.height / 2],
                [-self.length / 2, self.width / 2, self.height / 2],
                [self.length / 2, self.width / 2, self.height / 2],
                [self.length / 2, -self.width / 2, self.height / 2],
            ]
        )

    # Draw the BBox using verticies
    def draw_bbox(self, highlighted=0) -> None:
        self.set_axis_aligned_verticies()
        GL.glPushMatrix()

        # set colour
        bbox_color = (0, 0, 1, 1)
        if highlighted == 1:
            bbox_color = (0, 1, 0, 1)
        if highlighted == 2:
            bbox_color = (1, 0, 0, 1)
        if highlighted == 3:
            bbox_color = (0, 1, 1, 1)

        vertices = self.get_vertices()
        drawing_sequence = []
        for edge in BBOX_EDGES:
            for vertex_id in edge:
                drawing_sequence.append(vertices[vertex_id])

        oglhelper.draw_lines(drawing_sequence, color=bbox_color)
        GL.glPopMatrix()


    # Draw a relationship using verticies
    def draw_relationship(self, vertices1, highlighted=0) -> None:
        self.set_axis_aligned_verticies()
        GL.glPushMatrix()
        vertices2 = self.get_vertices()

        # set colour
        if highlighted == 1:
            bbox_color = (1, 1, 0, 1)
        if highlighted == 2:
            bbox_color = (0, 1, 0, 1)
        if highlighted == 3:
            bbox_color = (1, 0, 0, 1)

        # get centre points of all faces
        faces1, faces2 = {}, {}
        for side in BBOX_SIDES:
            x = sum(vertices1[i][0] for i in BBOX_SIDES[side])/4
            y = sum(vertices1[i][1] for i in BBOX_SIDES[side])/4
            z = sum(vertices1[i][2] for i in BBOX_SIDES[side])/4
            faces1[side] = [x,y,z]
        
            x = sum(vertices2[i][0] for i in BBOX_SIDES[side])/4
            y = sum(vertices2[i][1] for i in BBOX_SIDES[side])/4
            z = sum(vertices2[i][2] for i in BBOX_SIDES[side])/4
            faces2[side] = [x,y,z]

        # find the two closest faces
        min_dist = np.Inf
        key1, key2 = "", ""
        for i in faces1:
            for j in faces2:
                dist = self.sq_distance(faces1[i][0], faces1[i][1], 
                faces1[i][2], faces2[j][0], faces2[j][1], faces2[j][2])
                if dist < min_dist:
                    min_dist = dist
                    key1, key2 = i, j
                
        # get vertices from faces
        chosen_vertices1 = [vertices1[i] for i in BBOX_SIDES[key1]]
        chosen_vertices2 = [vertices2[i] for i in BBOX_SIDES[key2]]

        # connect all vertices
        permutations = [[chosen_vertices2[1], chosen_vertices2[2], chosen_vertices2[3], chosen_vertices2[0]],
        [chosen_vertices2[2], chosen_vertices2[3], chosen_vertices2[0], chosen_vertices2[1]],
        [chosen_vertices2[3], chosen_vertices2[0], chosen_vertices2[1], chosen_vertices2[2]]]

        vertice_pairs = [np.concatenate((chosen_vertices1, chosen_vertices2)),
        np.concatenate((chosen_vertices1, permutations[0])),
        np.concatenate((chosen_vertices1, permutations[1])),
        np.concatenate((chosen_vertices1, permutations[2]))]
        
        # draw
        drawing_sequence = []
        for edge in BBOX_EDGES:
            for i  in range(1):
                for vertex_id in edge:
                    drawing_sequence.append(vertice_pairs[i][vertex_id])

        oglhelper.draw_lines(drawing_sequence, color=bbox_color, line_width=4)
        GL.glPopMatrix()


    def draw_orientation(self, crossed_side: bool = True) -> None:
        # Get object coordinates for arrow
        arrow_length = self.length * 0.4
        bp2 = [arrow_length, 0, 0]
        first_edge = [
            arrow_length * 0.8,
            arrow_length * 0.3,
            0,
        ]  # TODO: Refactor to OGL helper
        second_edge = [arrow_length * 0.8, arrow_length * -0.3, 0]
        third_edge = [arrow_length * 0.8, 0, arrow_length * 0.3]

        GL.glPushMatrix()
        GL.glLineWidth(5)

        # Apply translation and rotation
        GL.glTranslate(*self.get_center())

        GL.glRotate(self.get_z_rotation(), 0.0, 0.0, 1.0)
        GL.glRotate(self.get_y_rotation(), 0.0, 1.0, 0.0)
        GL.glRotate(self.get_x_rotation(), 1.0, 0.0, 0.0)

        GL.glBegin(GL.GL_LINES)
        GL.glVertex3fv([0, 0, 0])
        GL.glVertex3fv(bp2)
        GL.glVertex3fv(bp2)
        GL.glVertex3fv(first_edge)
        GL.glVertex3fv(bp2)
        GL.glVertex3fv(second_edge)
        GL.glVertex3fv(bp2)
        GL.glVertex3fv(third_edge)
        if crossed_side:
            GL.glVertex3fv(self.verticies[BBOX_SIDES["right"][0]])
            GL.glVertex3fv(self.verticies[BBOX_SIDES["right"][2]])
            GL.glVertex3fv(self.verticies[BBOX_SIDES["right"][1]])
            GL.glVertex3fv(self.verticies[BBOX_SIDES["right"][3]])
        GL.glEnd()
        GL.glLineWidth(1)
        GL.glPopMatrix()

    # MANIPULATORS

    # Translate bbox by cx, cy, cz
    def translate_bbox(self, dx, dy, dz) -> None:
        self.center = math3d.translate_point(list(self.center), dx, dy, dz)

    # Translate bbox away from extension by half distance
    def translate_side(self, p_id_s, p_id_o, distance) -> None:
        direction = np.subtract(
            self.get_vertices()[p_id_s], self.get_vertices()[p_id_o]
        )
        translation_vector = direction / np.linalg.norm(direction) * (distance / 2)
        self.center = math3d.translate_point(self.center, *translation_vector)

    # Extend bbox side by distance
    def change_side(self, side, distance) -> None:  # ToDo: Move to controller?
        if side == "right" and self.length + distance > BBox.MIN_DIMENSION:
            self.length += distance
            self.translate_side(3, 0, distance)  # TODO: Make dependend from side list
        if side == "left" and self.length + distance > BBox.MIN_DIMENSION:
            self.length += distance
            self.translate_side(0, 3, distance)
        if side == "front" and self.width + distance > BBox.MIN_DIMENSION:
            self.width += distance
            self.translate_side(1, 0, distance)
        if side == "back" and self.width + distance > BBox.MIN_DIMENSION:
            self.width += distance
            self.translate_side(0, 1, distance)
        if side == "top" and self.height + distance > BBox.MIN_DIMENSION:
            self.height += distance
            self.translate_side(4, 0, distance)
        if side == "bottom" and self.height + distance > BBox.MIN_DIMENSION:
            self.height += distance
            self.translate_side(0, 4, distance)
