import itertools
import operator
import copy
import numpy as np

from .geometry import point_in_polygon
from .geometry import calc_intersection


class Fragment(object):
    """Fragment consists of a point array with identified endpoint.

    Props:
        point_array (np.ndarray): point array.
        is_inside (bool): this fragment is inside the counterpart or not.
        start_id (int): id for the start of point array.
        end_id (int): id fot the end of point array.
    """

    def __init__(self, point_array, is_inside, start_id, end_id):
        self.point_array = point_array
        self.is_inside = is_inside
        self.start_id = start_id
        self.end_id = end_id

    def __len__(self):
        return len(self.point_array)


class Boolean(object):
    """Performs boolean operation of two point array.

    Props:
        point_array1 (np.ndarray): existed point array to be merged.
        point_array2 (np.ndarray): newly drawn point array.
        fragments1 (Fragment): fragments of point_array1.
        fragments2 (Fragment): fragments of point_array2.
    """

    def __init__(self, point_array1, point_array2):
        self.point_array1 = point_array1
        self.point_array2 = point_array2

        self.fragments1 = None
        self.fragments2 = None

    def initialize(self):
        """calculates cross points of the two point arrays and divided them to
           fragments of which endpoints are obtained cross points.

        Returns:
            (bool): if the initialization succeeds, return True.
        """
        point_array1 = self.point_array1
        point_array2 = self.point_array2
        N1 = len(point_array1)
        N2 = len(point_array2)

        combine_idx = itertools.product(range(N1), range(N2))
        cross_points = []
        new_point_array1 = copy.deepcopy(point_array1)
        new_point_array2 = copy.deepcopy(point_array2)
        inserted_in_array1 = []
        inserted_in_array2 = []

        idx = 0
        for (i, j) in combine_idx:
            p1 = point_array1[i]
            p2 = point_array1[i + 1] if i != N1 - 1 else point_array1[0]
            p3 = point_array2[j]
            p4 = point_array2[j + 1] if j != N2 - 1 else point_array2[0]

            cross_point = calc_intersection(p1, p2, p3, p4)

            if cross_point is None:
                continue

            cross_point = np.array(cross_point)

            if not np.array_equal(cross_point, p1):
                inserted_in_array1.append(i)
                new_idx1 = i + 1 + sorted(inserted_in_array1).index(i)
                new_idx1 += inserted_in_array1.count(i) - 1
                new_point_array1 = np.insert(
                    new_point_array1, new_idx1, cross_point, axis=0
                )

            if not np.array_equal(cross_point, p3):
                inserted_in_array2.append(j)
                new_idx2 = j + 1 + sorted(inserted_in_array2).index(j)
                new_idx2 += inserted_in_array2.count(j) - 1
                new_point_array2 = np.insert(
                    new_point_array2, new_idx2, cross_point, axis=0
                )

            cross_points.append({
                'cp_idx': idx,
                'point': cross_point,
            })
            idx += 1

        if len(cross_points) == 0:
            return False

        if len(cross_points) % 2 != 0:
            return False

        for item in cross_points:
            cross_point = item['point']
            idx_i = np.apply_along_axis(
                lambda p: np.array_equal(p, cross_point), 1, new_point_array1
            )
            idx_i = np.where(idx_i)[0].item(0)

            idx_j = np.apply_along_axis(
                lambda p: np.array_equal(p, cross_point), 1, new_point_array2
            )
            idx_j = np.where(idx_j)[0].item(0)

            item.update({
                'i': idx_i,
                'j': idx_j,
            })

        self.point_array1 = new_point_array1
        self.point_array2 = new_point_array2
        self.fragments1 = self._divide_fragments(
            self.point_array1, cross_points, 'i'
        )
        self.fragments2 = self._divide_fragments(
            self.point_array2, cross_points, 'j'
        )
        return True

    def _divide_fragments(self, point_array, cross_points, ij):
        """divides point array to fragments.

        Args:
            point_array (np.ndarray): point array to be divided.
            cross_points (dict): information for the original cross points.
            ij (str): 'i' is for point_array1, 'j' is for point_array2.

        Returns:
            fragments (list): list of fragments.
        """
        N = len(point_array)
        sorted_idx = [item[ij] for item in sorted(
            cross_points, key=operator.itemgetter(ij)
        )]

        diff = (N - 1) - sorted_idx[-1]
        if diff > 0:
            idx = (np.arange(N) - diff + N) % N
            point_array = point_array[idx, :]
            for item in cross_points:
                temp = item[ij]
                item[ij] = (temp + diff) % N

        fragments = []
        cross_points = sorted(cross_points, key=operator.itemgetter(ij))

        for i, item in enumerate(cross_points):
            frag = Fragment(
                point_array[(cross_points[i - 1][ij] + 1) % N:item[ij] + 1],
                is_inside=None,
                start_id=cross_points[i - 1]['cp_idx'],
                end_id=cross_points[i]['cp_idx'],
            )
            frag.point_array = np.insert(
                frag.point_array, 0, cross_points[i - 1]['point'], axis=0
            )
            fragments.append(frag)

        length = [len(f) for f in fragments]
        max_idx = length.index(max(length))

        is_inside = None
        for i in range(len(fragments)):
            idx = (max_idx + i) % len(fragments)
            frag = fragments[idx]

            if is_inside is None:
                if ij == 'i':
                    target = self.point_array2
                elif ij == 'j':
                    target = self.point_array1

                point = frag.point_array[len(frag) // 2]
                is_inside = point_in_polygon(point, target)
            else:
                is_inside = not is_inside
            frag.is_inside = is_inside

        return fragments

    def merge(self, mode):
        """boolean operation (union or diffrence) by using fragments.

        Args:
            mode (str): 'union' or 'diff'.

        Returns:
            merged (np.ndarray): merged point array.
        """
        fragments1 = self.fragments1
        fragments2 = self.fragments2

        try:
            if fragments1[0].is_inside is True:
                fragments1 = fragments1[1::2]
            else:
                fragments1 = fragments1[0::2]

            if mode == 'union':
                if fragments2[0].is_inside is True:
                    fragments2 = fragments2[1::2]
                else:
                    fragments2 = fragments2[0::2]

            elif mode == 'diff':
                if fragments2[0].is_inside is True:
                    fragments2 = fragments2[0::2]
                else:
                    fragments2 = fragments2[1::2]

            merged = self._find_outer_line(fragments1, fragments2)
            if merged is None:
                merged = self._find_largest_hull(fragments1, fragments2)

            if merged.ndim == 1:
                return None

            if len(merged) > 2:
                return merged

            else:
                return None

        except Exception as e:
            print('BooleanMergeError: ', e.args)
            return None

    def _find_outer_line(self, fragments1, fragments2):
        """find outer line according to the boolean operation.

        Args:
            fragments1: list of fragments of point_array1.
            fragments2: list of fragments of point_array2.

        Returns:
            merged (np.ndarray): merged point array.
        """
        N = len(fragments2)

        merged = None
        if N == 1:
            frag = fragments2[0]
            joint = self._find_joint_fragment(
                fragments1, frag.end_id, frag.start_id
            )
            if joint is None:
                return None

            merged = frag.point_array[0:-1]
            merged = np.vstack((merged, joint.point_array[0:-1]))
            return merged

        else:
            for i in range(N):
                frag = fragments2[i]
                next = fragments2[i + 1] if i != N - 1 else fragments2[0]
                joint = self._find_joint_fragment(
                    fragments1, frag.end_id, next.start_id
                )
                if joint is None:
                    return None
                if merged is None:
                    merged = frag.point_array[0:-1]
                    merged = np.vstack((merged, joint.point_array[0:-1]))
                else:
                    merged = np.vstack((merged, frag.point_array[0:-1]))
                    merged = np.vstack((merged, joint.point_array[0:-1]))
            return merged

    def _find_joint_fragment(self, fragments, start_id, end_id):
        """finds fragments with can joint with a fragment of
           corresponding endpoints.

        Args:
            fragments: list of fragment.
            start_id: id of one endpoint.
            end_id: id of another endpoint.

        Returns:
            frag (Fragment): mached fragment.
        """
        query = set([start_id, end_id])

        for frag in fragments:
            start_end = set([frag.start_id, frag.end_id])
            if start_end == query:
                if end_id == frag.start_id:
                    frag.point_array = frag.point_array[::-1]
                return frag

    def _find_largest_hull(self, fragments1, fragments2):
        """finds largest hull after the boolean operation.

        Args:
            fragments1: one list of fragments.
            fragments2: another list of fragments.

        Returns:
            largest_hull: the largest hull of the merged point arrays.
        """

        N = len(fragments2)

        candidates = []
        for i in range(N):
            candidate = None
            frag = fragments2[i]
            joint = self._find_joint_fragment(
                fragments1, frag.end_id, frag.start_id
            )
            if joint is not None:
                if candidate is None:
                    candidate = frag.point_array[0:-1]
                    candidate = np.vstack((candidate, joint.point_array[0:-1]))
                else:
                    candidate = np.vstack((candidate, frag.point_array[0:-1]))
                    candidate = np.vstack((candidate, joint.point_array[0:-1]))
                candidates.append(candidate)

        length = [len(c) for c in candidates]
        largest_hull = candidates[length.index(max(length))]
        return largest_hull
