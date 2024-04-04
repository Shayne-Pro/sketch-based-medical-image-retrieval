import vtk
import copy
import math
import numpy as np
from operator import itemgetter
from PyQt5.QtCore import QSettings

from .utils import polydata_to_numpy
from .utils import make_line
from .utils import make_actor
from .utils import make_caption_actor
from .utils import make_rectangle
from .utils import get_axial_bound_area
from .utils import translate_polydata
from ..contour_module import point_in_polygon
from ..contour_module import remove_inline_crossover
from ..contour_module import Boolean
from ..utils.state import StateBase
from ..utils.state import StateBundler


ACTIVE_OPACITY = 0.6
INACTIVE_OPACITY = 0.4


def editable_state_only(func):
    def _editable_state_only(*args, **kwargs):
        is_editable = args[0].state['is_editable']
        if is_editable:
            return func(*args, **kwargs)
        else:
            raise Exception('This function is under editable state only.')
    return _editable_state_only


class ViewerController(object):

    def __init__(self, **kwargs):
        self.viewer_state = StateBase(**kwargs)
        self.state = StateBundler()
        self.state.add_state(self.viewer_state)
        self.brush_mode = None
        self.brush_prev_point = None

        self.Z_DEPTH = 0.0001
        self.BOLD = 5
        self.REGULAR = 2
        self.NARROW = 1
        self.TOLERANCE = 0.1

    def activate_editing(self, **kwargs):
        self.state['is_editable'] = True
        self.edit_state = StateBase(**kwargs)
        self.state.add_state(self.edit_state)

    @editable_state_only
    def inactivate_editing(self):
        if self.state['is_calc_dist']:
            self.stop_measure()

        viewer = self.state['viewer']
        self.remove_all_actors()
        viewer.Render()
        self.state['is_editable'] = False
        self.state.discard_state(self.edit_state)

    def pick_world_coordinate(self) -> 'np.ndarray':
        iren = self.state['iren']
        viewer = self.state['viewer']

        pos = iren.GetEventPosition()
        picker = vtk.vtkPropPicker()
        picker.Pick(pos[0], pos[1], 0, viewer.GetRenderer())
        point = np.array(picker.GetPickPosition())
        return point

    def refresh(self):
        viewer = self.state['viewer']
        if self.state['is_editable']:
            self.remove_all_actors()
            self.add_all_actors()

        viewer.Render()

    def start_measure(self):
        self.state['is_calc_dist'] = True
        self.dist_line = StateBase(dist_line=None)
        self.state.add_state(self.dist_line)
        self.refresh()

    def stop_measure(self):
        self.draw_dist_line('CLEAR')
        self.state.discard_state(self.dist_line)
        self.state['is_calc_dist'] = False

    @editable_state_only
    def get_active_structure(self):
        struct = self.state['structure_list'][self.state['structure_idx']]
        return struct

    @editable_state_only
    def change_active_structure(self, structure_idx):
        viewer = self.state['viewer']

        self.state['structure_idx'] = structure_idx

        self.refresh()

    @editable_state_only
    def delete_active_contour(self):
        viewer = self.state['viewer']
        struct = self.get_active_structure()
        if len(struct.contour_indices) == 1:
            return

        idx = struct.contour_idx
        for slice in struct.contours.keys():
            indices = struct.contours[slice].keys()
            if len(indices) > 0:
                if idx in indices:
                    actor = struct.get_actor(slice, idx)
                    if actor is not None:
                        viewer.GetRenderer().RemoveActor(actor)
                    del struct.contours[slice][idx]

        for slice in list(struct.contours.keys()):
            if len(struct.contours[slice]) == 0:
                del struct.contours[slice]

        struct.contour_indices.remove(idx)
        next_idx = min(struct.contour_indices)
        self.change_active_contour(next_idx)

    @editable_state_only
    def add_active_contour(self):
        struct = self.get_active_structure()
        last_idx = struct.contour_indices[-1]
        if struct.is_empty_contour(last_idx):
            self.change_active_contour(last_idx)
            return

        next_idx = max(struct.contour_indices) + 1
        struct.contour_indices.append(next_idx)
        self.change_active_contour(next_idx)

    @editable_state_only
    def change_active_contour(self, idx):
        struct = self.get_active_structure()
        struct.contour_idx = idx
        # self.update_text_actor()
        self.refresh()

    @editable_state_only
    def change_active_contour_to_next(self):
        struct = self.get_active_structure()
        n = len(struct.contour_indices)
        current_idx = struct.contour_indices.index(struct.contour_idx)
        next_idx = (current_idx + 1) % n

        struct.contour_idx = struct.contour_indices[next_idx]
        # self.update_text_actor()
        self.refresh()

    @editable_state_only
    def remove_contour_in_slice(self):
        viewer = self.state['viewer']
        struct = self.get_active_structure()
        actor = struct.get_actor()
        if actor is not None:
            viewer.GetRenderer().RemoveActor(actor)
            struct.del_contour()
            self.refresh()

    @editable_state_only
    def get_structure_on_mouse(self):
        point = self.pick_world_coordinate()
        slice = self.state['slice']

        for structure_idx, structure in enumerate(self.state['structure_list']):
            if slice in structure.contours.keys():
                for contour_idx in structure.contours[slice].keys():
                    point_list = structure.contours[slice][contour_idx]['points']

                    if point_in_polygon(point, point_list):
                        return structure_idx, contour_idx

        return None, None

    @editable_state_only
    def get_next_structure_idx(self):
        n = len(self.state['structure_list'])
        current_idx = self.state['structure_idx']
        next_idx = (current_idx + 1) % n

        return next_idx

    @editable_state_only
    def add_all_actors(self, fill_inside=False):
        slice = self.state['slice']
        viewer = self.state['viewer']
        structure_list = self.state['structure_list']

        for structure_idx, struct in enumerate(structure_list):
            if structure_idx == self.state['structure_idx']:
                is_active_struct = True
            else:
                is_active_struct = False

            if slice in struct.contours.keys():
                indices = struct.contours[slice].keys()
                if len(indices) > 0:
                    for idx in indices:

                        actor = struct.get_actor(slice, idx)
                        if actor is not None:

                            if idx == struct.contour_idx:
                                is_active_contour = True
                            else:
                                is_active_contour = False

                            if is_active_struct and is_active_contour:
                                actor.GetProperty().SetLineWidth(self.BOLD)
                                actor.GetProperty().SetOpacity(ACTIVE_OPACITY)
                            else:
                                actor.GetProperty().SetLineWidth(self.REGULAR)
                                actor.GetProperty().SetOpacity(INACTIVE_OPACITY)

                            viewer.GetRenderer().AddActor(actor)

    @editable_state_only
    def remove_all_actors(self):
        slice = self.state['slice']
        viewer = self.state['viewer']
        # self.remove_helper_actors()

        for struct in self.state['structure_list']:
            if slice in struct.contours.keys():
                indices = struct.contours[slice].keys()
                if len(indices) > 0:
                    for idx in indices:
                        actor = struct.get_actor(slice, idx)
                        if actor is not None:
                            viewer.GetRenderer().RemoveActor(actor)

    ###############################################################################
    # Draw functions
    ###############################################################################

    @editable_state_only
    def increase_brush_size(self):
        size = self.state['brush_size']
        if size < self.state['max_brush_size']:
            self.state['brush_size'] += 0.5

    @editable_state_only
    def decrease_brush_size(self):
        size = self.state['brush_size']
        if size > self.state['min_brush_size']:
            self.state['brush_size'] -= 0.5

    @editable_state_only
    def draw_line(self, finalize):
        viewer = self.state['viewer']
        struct = self.get_active_structure()
        point = self.pick_world_coordinate()

        struct.add_temp_points(point, self.TOLERANCE)

        if not finalize:
            if not struct.has_valid_temp_points_length():
                return

            temp_line = make_line(struct.temp_points, close=False)
            temp_line = translate_polydata(temp_line, 0, 0, self.Z_DEPTH)
            temp_actor = make_actor(temp_line, struct.color, self.BOLD, opacity=None, fill_inside=False)
            if struct.temp_actor is not None:
                viewer.GetRenderer().RemoveActor(struct.temp_actor)
            viewer.GetRenderer().AddActor(temp_actor)
            viewer.Render()
            struct.temp_actor = temp_actor
            return

        # finalize.
        struct.simplify_temp_points()
        if not struct.has_valid_temp_points_length():
            viewer.GetRenderer().RemoveActor(struct.temp_actor)
            viewer.Render()
            struct.reset_temp_contour()
            return

        # draw once.
        temp_line = make_line(struct.temp_points, close=True)
        temp_line = translate_polydata(temp_line, 0, 0, self.Z_DEPTH)
        temp_actor = make_actor(temp_line, struct.color, self.BOLD)

        if struct.temp_actor is not None:
            viewer.GetRenderer().RemoveActor(struct.temp_actor)
        viewer.GetRenderer().AddActor(temp_actor)
        viewer.Render()
        struct.temp_actor = temp_actor

        existed_contour = struct.get_contour()

        # if this is first draw, register temporary points to contour.
        if existed_contour is None:
            struct.register_contour(struct.temp_points, struct.temp_actor)
            struct.reset_temp_contour()
            return

        # merge temporary points to existed points.
        existed_points = existed_contour['points']
        existed_actor = existed_contour['actor']

        start_point = struct.temp_points[0]
        if point_in_polygon(start_point, existed_points):
            mode = 'union'
        else:
            mode = 'diff'

        self.process_boolean(mode, existed_points, existed_actor,
                             struct.temp_points, struct.temp_actor)

    @editable_state_only
    def draw_brush(self, point, mode):
        viewer = self.state['viewer']
        struct = self.get_active_structure()
        size = self.state['brush_size']

        if struct.temp_center is None:
            struct.temp_center = point

        else:
            if not struct.has_valid_center_distance(point, self.TOLERANCE):
                return mode

        circle = vtk.vtkRegularPolygonSource()
        num_sides = int(size * 3.14)

        if num_sides < 10:
            num_sides = 10
        elif num_sides > 30:
            num_sides = 30

        circle.SetNumberOfSides(num_sides)
        circle.SetRadius(size)
        circle.SetCenter(point)
        circle.Update()

        struct.temp_points = polydata_to_numpy(circle.GetOutput())

        # draw ones.
        temp_circle = make_line(struct.temp_points, close=True)
        temp_circle = translate_polydata(temp_circle, 0, 0, self.Z_DEPTH)
        temp_actor = make_actor(temp_circle, struct.color, self.BOLD)

        if struct.temp_actor is not None:
            viewer.GetRenderer().RemoveActor(struct.temp_actor)
        viewer.GetRenderer().AddActor(temp_actor)
        viewer.Render()
        struct.temp_actor = temp_actor

        existed_contour = struct.get_contour()

        # if this is first draw, register temporary points to contour.
        if existed_contour is None:
            struct.register_contour(struct.temp_points, struct.temp_actor)
            struct.reset_temp_contour()
            return 'union'

        # merge temporary points to existed points.
        existed_points = existed_contour['points']
        existed_actor = existed_contour['actor']

        if mode is None:
            if point_in_polygon(point, existed_points):
                mode = 'union'
            else:
                mode = 'diff'

        self.process_boolean(mode, existed_points, existed_actor,
                             struct.temp_points, struct.temp_actor)
        return mode

    @editable_state_only
    def process_draw_brush(self):
        point = self.pick_world_coordinate()
        prev = self.brush_prev_point
        self.brush_prev_point = point

        if prev is None:
            self.brush_mode = self.draw_brush(point, self.brush_mode)
        else:
            distance = np.linalg.norm(point - prev)
            split_num = min(5, int(np.ceil(distance / 5)))
            for i in range(split_num):
                self.draw_brush(prev + (point - prev) * (i + 1) / split_num, self.brush_mode)

    @editable_state_only
    def end_draw_brush(self):
        self.process_draw_brush()
        self.brush_mode = None
        self.brush_prev_point = None

    @editable_state_only
    def process_boolean(self, mode, existed_points, existed_actor, temp_points, temp_actor):
        viewer = self.state['viewer']
        struct = self.get_active_structure()

        bool = Boolean(existed_points, temp_points)
        if bool.initialize():
            merged_points = bool.merge(mode=mode)
            if merged_points is not None:
                merged_line = make_line(merged_points, close=True)
                area = get_axial_bound_area(merged_line)

                if area > self.state['tolerance_area']:
                    merged_line = translate_polydata(
                        merged_line, 0, 0, self.Z_DEPTH)
                    merged_actor = make_actor(merged_line, struct.color, self.BOLD)
                    viewer.GetRenderer().RemoveActor(existed_actor)
                    viewer.GetRenderer().RemoveActor(temp_actor)
                    viewer.GetRenderer().AddActor(merged_actor)
                    viewer.Render()
                    struct.register_contour(merged_points, merged_actor)
                    struct.reset_temp_contour()
                    return

                else:
                    viewer.GetRenderer().RemoveActor(existed_actor)
                    viewer.GetRenderer().RemoveActor(temp_actor)
                    viewer.Render()
                    struct.reset_temp_contour()
                    struct.del_contour()
                    return

        # failure in boolean operation.
        viewer.GetRenderer().RemoveActor(temp_actor)
        viewer.Render()
        struct.reset_temp_contour()

    def draw_dist_line(self, state):
        viewer = self.state['viewer']
        point = self.pick_world_coordinate()
        dist_line = self.state['dist_line']
        if dist_line == None:
            dist_line = {}

        if state == 'START':
            dist_line['points'] = [point, point]
            if 'line_actor' in dist_line and dist_line['line_actor'] is not None:
                viewer.GetRenderer().RemoveActor(dist_line['line_actor'])
                viewer.GetRenderer().RemoveActor(dist_line['text_actor'])
                viewer.Render()
                dist_line['line_actor'] = None
                dist_line['text_actor'] = None

        elif state == 'DRAWING' and 'points' in dist_line and dist_line['points']:
            dist_line['points'][1] = point
            temp_line = make_line(dist_line['points'], close=True)
            temp_line = translate_polydata(temp_line, 0, 0, self.Z_DEPTH)
            line_actor = make_actor(temp_line, width=self.REGULAR,
                                    color=vtk.vtkNamedColors().GetColor3d("Tomato"),
                                    opacity=None, fill_inside=False)
            # キャプション表示位置を計算
            (min_x, max_x, min_y, max_y, min_z, max_z) = temp_line.GetBounds()
            x = ((max_x + min_x)/2)
            y = ((max_y + min_y)/2)
            z = min_z
            # 距離を計算
            dist = (max_x - min_x) * (max_x - min_x)
            dist += (max_y - min_y) * (max_y - min_y)
            dist = math.sqrt(dist)
            text_actor = make_caption_actor((x, y, z), "{:,.2f}mm".format(dist), size=14,
                                    color=vtk.vtkNamedColors().GetColor3d("Tomato"))
            if 'line_actor' in dist_line and dist_line['line_actor'] is not None:
                viewer.GetRenderer().RemoveActor(dist_line['line_actor'])
                viewer.GetRenderer().RemoveActor(dist_line['text_actor'])
            viewer.GetRenderer().AddActor(line_actor)
            viewer.GetRenderer().AddActor(text_actor)
            viewer.Render()
            dist_line['line_actor'] = line_actor
            dist_line['text_actor'] = text_actor

        elif state == 'END':
            dist_line['points'] = None
        elif state == 'CLEAR':
            if 'line_actor' in dist_line and dist_line['line_actor'] is not None:
                viewer.GetRenderer().RemoveActor(dist_line['line_actor'])
                viewer.GetRenderer().RemoveActor(dist_line['text_actor'])
                viewer.Render()
                dist_line['line_actor'] = None
                dist_line['text_actor'] = None
            dist_line['points'] = None

        self.state['dist_line'] = dist_line

    ###############################################################################
    # Handling images
    ###############################################################################

    def update_image_window(self, window_width, window_center):
        viewer = self.state['viewer']
        viewer.SetColorWindow(window_width)
        viewer.SetColorLevel(window_center)
        self.refresh()
