import vtk
import numpy as np
import json


def read_niigz(path, dataset_type):
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(path)
    reader.Update()

    image = reader.GetOutput()

    (xMin, xMax, yMin, yMax, zMin, zMax) = image.GetExtent()
    (xSpacing, ySpacing, zSpacing) = image.GetSpacing()
    (x0, y0, z0) = image.GetOrigin()

    center = [x0 + xSpacing * 0.5 * (xMin + xMax),
              y0 + ySpacing * 0.5 * (yMin + yMax),
              z0 + zSpacing * 0.5 * (zMin + zMax)]

    axial = vtk.vtkMatrix4x4()

    if dataset_type == 'MICCAI_BraTS':
        axial.DeepCopy((-1, 0, 0, center[0],
                        0, -1, 0, center[1],
                        0, 0, -1, center[2],
                        0, 0, 0, 1))
    else:
        raise NotImplementedError(
            'Only the MICCAI BraTS 2019 dataset is available in the public version.')

    reslice = vtk.vtkImageReslice()
    reslice.SetInputData(image)
    reslice.SetResliceAxes(axial)
    reslice.Update()

    image = reslice.GetOutput()

    return image


def z_score_normalize(array):
    array = array.astype(np.float32)
    mask = array > 0
    mean = np.mean(array[mask])
    std = np.std(array[mask])
    array -= mean
    array /= std
    return array
