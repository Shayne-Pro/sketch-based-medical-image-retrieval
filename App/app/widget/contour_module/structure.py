import copy
import numpy as np
from collections import defaultdict

from ..vtk_module.utils import make_line
from ..vtk_module.utils import make_actor
from ..vtk_module.utils import translate_polydata
from .geometry import remove_inline_crossover


# TOLERANCE = 1.0
Z_DEPTH = 0.0001


class Structure(object):
    """Structure class for each instance annotation.
       One structure can retain multiple contours in a plane.

    Props:
        idx (int): counter for the number of instantiation.
        class_name (str): class name.
        name (str): editable instance name.
        color (tuple): color of the structure.
        contours: dictionaly containing contour information.
            contours[slice][contour_idx] = {
                'points': np.ndarray,
                'actor': vtkActor,
            }
        contour_idx (int): index of the contour.
        ref_state (ViewerState): referenced state of the viewer.
        temp_center (np.ndarray): temporary center in brush editing.
        temp_start_point (np.ndarray): temporary start point in box editing.
        temp_actor (vtkActor): temporary actor.
        temp_points (np.ndarray): temporary point array.
    """
    count = 0

    def __init__(self, class_name, name, color, ref_state):
        self.idx = self.counter()
        self.class_name = class_name
        self.name = name
        self.color = color
        self.contours = defaultdict(lambda: defaultdict(dict))
        self.contour_indices = [0]
        self.contour_idx = 0
        self.ref_state = ref_state
        self.temp_center = None
        self.temp_start_point = None
        self.temp_actor = None
        self.temp_points = None

    @classmethod
    def init_from_config(cls, config, ref_state):

        structure = cls(
            class_name=config['class_name'],
            name=config['name'],
            color=config['color'],
            ref_state=ref_state
        )

        structure.idx = config['idx']
        structure.contour_indices = config['contour_indices']
        structure.contour_idx = structure.contour_indices[0]

        if len(config['contours'].keys()) > 0:

            for slice in config['contours']:
                for contour_idx in config['contours'][slice]:
                    points = np.array(config['contours'][slice][contour_idx])
                    polygon = make_line(points, close=True)
                    # z_position = slice_locations[slice]
                    polygon = translate_polydata(polygon, 0, 0, Z_DEPTH)
                    actor = make_actor(polygon, color=structure.color)
                    structure.contours[int(slice)][int(contour_idx)] = {
                        'points': points,
                        'actor': actor
                    }

        return structure

    def serialize(self):
        contours = defaultdict(lambda: defaultdict(list))

        for slice in self.contours.keys():
            for contour_idx in self.contours[slice].keys():
                points = self.contours[slice][contour_idx]['points']
                if points is not None:
                    contours[slice][contour_idx] = points.tolist()

        structure = {
            'idx': self.idx,
            'class_name': self.class_name,
            'name': self.name,
            'color': self.color,
            'contours': contours,
            'contour_indices': self.contour_indices,
            'slice_locations': self.ref_state['slice_locations'],
        }

        return structure

    def load(self, config):
        self.idx = config['idx']
        self.color = config['color']
        self.contour_indices = config['contour_indices']
        # slice_locations = config['slice_locations']

        for slice in config['contours']:
            for contour_idx in config['contours'][slice]:
                points = np.array(config['contours'][slice][contour_idx])
                polygon = make_line(points, close=True)
                # z_position = slice_locations[slice]
                polygon = translate_polydata(polygon, 0, 0, Z_DEPTH)
                actor = make_actor(polygon, color=self.color)
                self.contours[int(slice)][int(contour_idx)] = {
                    'points': points,
                    'actor': actor
                }

    @classmethod
    def counter(cls):
        """counter of the number of instantiation.
        """
        cls.count += 1
        return cls.count

    def add_temp_points(self, point, TOLERANCE: float):
        """adds point to the temporary point array.

        Args:
            point (np.ndarray): next point to be added.
        """
        if self.temp_points is None:
            self.temp_points = point
        else:
            if self.temp_points.ndim > 1:
                for existed in self.temp_points[::-1]:
                    d = np.linalg.norm(existed - point)
                    if d < TOLERANCE:
                        return
            self.temp_points = np.vstack((self.temp_points, point))

    def has_valid_center_distance(self, point, TOLERANCE: float):
        """checks if the next center has enough distance to be added.

        Args:
            point (np.ndarray): next center to be added.
        """
        d = np.linalg.norm(self.temp_center, point)
        if d < TOLERANCE:
            return False
        else:
            return True

    def has_valid_temp_points_length(self):
        """checks if the temporary point set has enough length to be an actor.
        """
        if self.temp_points.ndim == 1:
            return False
        if len(self.temp_points) > 2:
            return True
        else:
            return False

    def simplify_temp_points(self):
        """simplifies the temporary point array by removing inline crossovers.
        """
        if self.temp_points.ndim == 1:
            return
        self.temp_points = remove_inline_crossover(self.temp_points)

    def get_contour(self, slice=None, idx=None):
        """gets the contour information.

        Args:
            slice (int): the number of slice.
            idx (int): index of the contour.
        """
        if slice is None:
            slice = self.ref_state['slice']
        if idx is None:
            idx = self.contour_idx
        if slice in self.contours.keys():
            if idx in self.contours[slice].keys():
                return self.contours[slice][idx]

    def get_actor(self, slice=None, idx=None):
        """gets actor.

        Args:
            slice (int): the number of slice.
            idx (int): index of the contour.
        """
        if slice is None:
            slice = self.ref_state['slice']
        if idx is None:
            idx = self.contour_idx
        if slice in self.contours.keys():
            if idx in self.contours[slice].keys():
                return self.contours[slice][idx]['actor']

    def get_points(self, slice=None, idx=None):
        """gets point array.

        Args:
            slice (int): the number of slice.
            idx (int): index of the contour.
        """
        if slice is None:
            slice = self.ref_state['slice']
        if idx is None:
            idx = self.contour_idx
        if slice in self.contours.keys():
            if idx in self.contours[slice].keys():
                return self.contours[slice][idx]['points']

    def get_all_points(self, slice=None):
        """gets an array of point arrays.

        Args:
            slice (int): the number of slice.
        """
        if slice is None:
            slice = self.ref_state['slice']

        if slice in self.contours.keys():
            all_points = []
            for idx in self.contours[slice].keys():
                all_points.append(self.contours[slice][idx]['points'])

            if len(all_points) > 0:
                return all_points

    def del_contour(self, slice=None, idx=None):
        """deletes the contour information.

        Args:
            slice (int): the number of slice.
            idx (int): index of the contour.
        """
        if slice is None:
            slice = self.ref_state['slice']
        if idx is None:
            idx = self.contour_idx
        if slice in self.contours.keys():
            if idx in self.contours[slice].keys():
                del self.contours[slice][idx]

    def reset_temp_contour(self):
        """resets temporary contour information.
        """
        self.temp_center = None
        self.temp_start_point = None
        self.temp_actor = None
        self.temp_points = None

    def register_contour(self, points, actor, slice=None, idx=None):
        """registers point array and actor to the structure.

        Args:
            points (np.ndarray): point array to be registered.
            actor (vtkActor): actor to be registered.
            slice (int): the number of slice.
            idx (int): index of the contour.
        """
        if slice is None:
            slice = self.ref_state['slice']
        if idx is None:
            idx = self.contour_idx
        self.contours[slice][idx].update({
            'points': copy.deepcopy(points),
            'actor': actor,
        })

    def is_empty_contour(self, contour_idx):
        """checks if the contour is empty or not.

        Args:
            contour_idx: index of contour to be checked.

        Returns:
            (bool): if the contour is empty, return True.
        """
        for slice in self.contours.keys():
            indices = self.contours[slice].keys()
            if len(indices) > 0:
                if contour_idx in indices:
                    return False
        return True

    def is_empty(self):
        is_empty = True
        for slice in self.contours.keys():
            indices = self.contours[slice].keys()
            if len(indices) > 0:
                for idx in indices:
                    points = self.contours[slice][idx]['points']
                    if len(points) > 0:
                        is_empty = False
                        break
        return is_empty
