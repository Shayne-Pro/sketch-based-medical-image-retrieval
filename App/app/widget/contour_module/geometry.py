import numpy as np

from .c_geometry.geometry import c_judge_parallel
from .c_geometry.geometry import c_calc_intersection
from .c_geometry.geometry import c_point_in_polygon
from .c_geometry.geometry import c_remove_inline_crossover


def judge_parallel(p1, p2, p3, p4):
    return c_judge_parallel(p1, p2, p3, p4)


def calc_intersection(p1, p2, p3, p4):
    return c_calc_intersection(p1, p2, p3, p4)


def point_in_polygon(point, point_list):
    return c_point_in_polygon(point, point_list)


def remove_inline_crossover(point_list):
    return c_remove_inline_crossover(point_list)


def p_judge_parallel(p1, p2, p3, p4):
    """Judges if two line segments (A and B) are parallel or not.

    Args:
        p1: endpoint of segment A.
        p2: another endpoint of segment A.
        p3: endpoint of segment B.
        p4: another endpoint of segment B.
    """
    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if d == 0:
        return True
    else:
        return False


def p_calc_intersection(p1, p2, p3, p4):
    """Detects where two line segments (A and B) intersect.

    Args:
        p1: endpoint of segment A.
        p2: another endpoint of segment A.
        p3: endpoint of segment B.
        p4: another endpoint of segment B.

    Returns:
        intersect: point of intersection.
    """
    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if d == 0:
        return None
    u = (p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])
    u /= d
    v = (p3[0] - p1[0]) * (p2[1] - p1[1]) - (p3[1] - p1[1]) * (p2[0] - p1[0])
    v /= d
    if u < 0.0 or u >= 1.0:
        return None
    if v < 0.0 or v >= 1.0:
        return None
    ix = p1[0] + u * (p2[0] - p1[0])
    iy = p1[1] + u * (p2[1] - p1[1])
    intersect = (ix, iy, p1[2])
    return intersect


def p_point_in_polygon(point, point_list):
    """Judges if a given point in the plane lies inside of a polygon or not.

    Args:
        point: point to be checked.

    Returns:
        inside: if the point is inside the polygon, returns True.
    """
    N = len(point_list)
    inside = False
    x, y, z = point
    p1x, p1y, p1z = point_list[0]
    for i in range(N + 1):
        p2x, p2y, p2z = point_list[i % N]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def p_remove_inline_crossover(point_list):
    """Removes extra crossover and returns one closed area.

    Args:
        point_list: a list of points.

    Returns:
        point_list: cleaned list of points as a one closed area.
    """
    N = len(point_list)
    for i in range(N - 1):
        p1 = point_list[i]
        p2 = point_list[i + 1]
        for j in range(i + 2, N):
            p3 = point_list[j]
            p4 = point_list[j + 1] if j != N - 1 else point_list[0]

            if i == 0 and j == N - 1:
                continue
            if calc_intersection(p1, p2, p3, p4):
                point_list = np.delete(point_list, np.s_[i + 1:j + 1:1], 0)
                return p_remove_inline_crossover(point_list)
    return point_list
