import numpy as np
import pyopencl
from pyopencl import mem_flags


opencl_src = '''
__kernel void _make_masked_image
(
    __global float* X,
    __global float* Y,
    __global float* polygon,
    __global uchar* out,
    int n
)
{
    const int r = get_global_id(0);
    const int c = get_global_id(1);
    float x = X[r];
    float y = Y[c];
    const int base = c * get_global_size(1) + r;
    int i, j, inside = 0;

    for (i = 0, j = n-1; i < n; j = i++) {
        float vertxi = polygon[3 * i];
        float vertxj = polygon[3 * j];
        float vertyi = polygon[3 * i + 1];
        float vertyj = polygon[3 * j + 1];
        if (((vertyi > y) != (vertyj > y)) &&
            (x < (vertxj-vertxi) * (y-vertyi) / (vertyj-vertyi) + vertxi)) {
                inside = !inside;
            }
    }
    out[base] = inside;
}
'''


def make_masked_image(contours,
                      masked_image,
                      value,
                      rows,
                      columns,
                      imagePosPat,
                      pixelSpacing):
    """
    Make masked image from a contour exported from dirom-rt,
    implemented on the GPGPU basis using pyopencl.
    """
    x = np.arange(rows).astype(np.float32)
    x *= pixelSpacing[0]
    x += imagePosPat[0]

    y = np.arange(columns).astype(np.float32)
    y *= pixelSpacing[1]
    y += imagePosPat[1]

    for contour in contours:
        poly = np.array(contour).astype(np.float32)
        numPoints = np.int32(poly.shape[0])
        context = pyopencl.create_some_context(interactive=False)
        queue = pyopencl.CommandQueue(context)
        x_buf = pyopencl.Buffer(context,
                                mem_flags.READ_ONLY |
                                mem_flags.COPY_HOST_PTR,
                                hostbuf=x)
        y_buf = pyopencl.Buffer(context,
                                mem_flags.READ_ONLY |
                                mem_flags.COPY_HOST_PTR,
                                hostbuf=y)
        poly_buf = pyopencl.Buffer(context,
                                   mem_flags.READ_ONLY |
                                   mem_flags.COPY_HOST_PTR,
                                   hostbuf=poly)
        out = np.zeros((rows, columns)).astype(np.uint8)
        out_buf = pyopencl.Buffer(context, mem_flags.WRITE_ONLY, out.nbytes)
        program = pyopencl.Program(context, opencl_src).build()
        program._make_masked_image(queue,
                                   (rows, columns),
                                   None,
                                   x_buf,
                                   y_buf,
                                   poly_buf,
                                   out_buf,
                                   numPoints)
        event = pyopencl.enqueue_copy(queue, out, out_buf)
        event.wait()

        out *= value
        # [NOTICE] In the same pixel, labels with smaller values are
        # replaced by labels with larger values, thus each label value
        # should reflect an anatomical hierarchy.
        diff_mask = out > masked_image
        masked_image[diff_mask] = value

    return masked_image[::-1, :]
