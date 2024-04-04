cimport cython
import numpy as np
cimport numpy as np


ctypedef np.float64_t DOUBLE_t
ctypedef np.int16_t SHORT_t


def c_judge_parallel(np.ndarray[DOUBLE_t, ndim=1, mode='c'] p1,
                     np.ndarray[DOUBLE_t, ndim=1, mode='c'] p2,
                     np.ndarray[DOUBLE_t, ndim=1, mode='c'] p3,
                     np.ndarray[DOUBLE_t, ndim=1, mode='c'] p4):

    cdef double d

    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    return d == 0


cpdef c_calc_intersection(np.ndarray[DOUBLE_t, ndim=1, mode='c'] p1,
                          np.ndarray[DOUBLE_t, ndim=1, mode='c'] p2,
                          np.ndarray[DOUBLE_t, ndim=1, mode='c'] p3,
                          np.ndarray[DOUBLE_t, ndim=1, mode='c'] p4):

    cdef double d
    cdef double u
    cdef double v
    cdef double ix
    cdef double iy

    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if d == 0:
        return None
    u = ((p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])) / d
    v = ((p3[0] - p1[0]) * (p2[1] - p1[1]) - (p3[1] - p1[1]) * (p2[0] - p1[0])) / d
    if u < 0.0 or u >= 1.0:
        return None
    if v < 0.0 or v >= 1.0:
        return None
    ix = p1[0] + u * (p2[0] - p1[0])
    iy = p1[1] + u * (p2[1] - p1[1])
    return (ix, iy, p1[2])


cpdef c_point_in_polygon(np.ndarray[DOUBLE_t, ndim=1, mode='c'] point,
                         np.ndarray[DOUBLE_t, ndim=2, mode='c'] point_array):

    cdef int N
    cdef int i
    cdef int inside
    cdef double p1x
    cdef double p1y
    cdef double p1z
    cdef double p2x
    cdef double p2y
    cdef double p2z
    cdef double x
    cdef double y
    cdef double z
    cdef double xinters

    x, y, z = point
    N = len(point_array)
    inside = -1
    p1x, p1y, p1z = point_array[0]
    for i in range(N + 1):
        p2x, p2y, p2z = point_array[i % N]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside *= -1
        p1x, p1y = p2x, p2y
    return inside > 0


cpdef c_remove_inline_crossover(np.ndarray[DOUBLE_t, ndim=2, mode='c'] point_array):

    cdef int N
    cdef int i
    cdef int j
    cdef np.ndarray[DOUBLE_t, ndim=1, mode='c'] p1
    cdef np.ndarray[DOUBLE_t, ndim=1, mode='c'] p2
    cdef np.ndarray[DOUBLE_t, ndim=1, mode='c'] p3
    cdef np.ndarray[DOUBLE_t, ndim=1, mode='c'] p4

    N = len(point_array)
    for i in range(N - 1):
        p1 = point_array[i]
        p2 = point_array[i + 1]
        for j in range(i + 2, N):
            p3 = point_array[j]
            p4 = point_array[j + 1] if j != N - 1 else point_array[0]
            if i == 0 and j == N - 1:
                continue
            if c_calc_intersection(p1, p2, p3, p4):
                point_array = np.delete(point_array, np.s_[i+1:j+1:1], 0)
                return c_remove_inline_crossover(point_array)
    return point_array


cpdef c_point_in_polygon_v2(int x,
                            int y,
                            np.ndarray[DOUBLE_t, ndim=2, mode='c'] point_array):

    cdef int N
    cdef int i
    cdef int inside
    cdef double p1x
    cdef double p1y
    cdef double p1z
    cdef double p2x
    cdef double p2y
    cdef double p2z
    cdef double xinters

    N = len(point_array)
    inside = -1
    p1x, p1y, p1z = point_array[0]
    for i in range(N + 1):
        p2x, p2y, p2z = point_array[i % N]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside *= -1
        p1x, p1y = p2x, p2y
    return inside > 0


cpdef c_make_mask_image(np.ndarray[SHORT_t, ndim=2, mode='c'] mask_image,
                        np.ndarray[DOUBLE_t, ndim=2, mode='c'] point_array,
                        int x_min,
                        int x_max,
                        int y_min,
                        int y_max):

    cdef int x
    cdef int y
    cdef int xs
    cdef int ys

    x = mask_image.shape[0]
    y = mask_image.shape[1]

    x_max = x_max + 1 if x_max + 1 < x else x_max
    y_max = y_max + 1 if y_max + 1 < y else y_max

    for xs in range(x_min, x_max):
        for ys in range(y_min, y_max):
            mask_image[xs, ys] = c_point_in_polygon_v2(xs, ys, point_array)

    return mask_image
