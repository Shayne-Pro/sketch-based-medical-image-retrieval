import os
import vtk
import numpy as np
import pydicom as dicom
from pydicom.dataset import Dataset
from pydicom.dataset import FileDataset
from vtk.util import numpy_support


def read_vtk(path):
    """Reads vtkPolyData.

    Args:
        path: path of vtkPolyData.

    Returns:
        polydata: vtkPolyData.
    """
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(path)
    reader.Update()
    polydata = reader.GetOutput()
    return polydata


def save_vtk(polydata, path):
    """Saves vtkPolyData.

    Args:
        polydata: vtkPolyData to save.
        path: path of vtkPolyData.
    """
    writer = vtk.vtkPolyDataWriter()
    writer.SetInput(polydata)
    writer.SetFileName(path)
    writer.Write()


def read_vti(path):
    """Reads vtkImageData.

    Args:
        path: path of vtkImageData.

    Returns:
        image: vtkImageData.
    """
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(path)
    reader.Update()
    image = reader.GetOutput()
    return image


def save_vti(image, path):
    """Saves vtkImageData.

    Args:
        polydata: vtkImageData to save.
        path: path of vtkImageData.
    """
    writer = vtk.vtkXMLImageDataWriter()
    writer.SetInput(image)
    writer.SetFileName(path)
    writer.Write()


def read_3darray(array, spacing=[1.0, 1.0, 1.0], origin=[0.0, 0.0, 0.0]):
    """Reads numpy.ndarray and converts it to vtkImageData.

    Args:
        array: 3D numpy.ndarray.

    Returns:
        image: vtkImageData.
    """
    assert array.ndim == 3
    array = array.transpose(2, 1, 0)
    dim = array.shape

    array = array.astype('uint8')
    array = array.tostring()

    importer = vtk.vtkImageImport()
    importer.CopyImportVoidPointer(array, len(array))
    importer.SetDataScalarType(vtk.VTK_UNSIGNED_CHAR)
    importer.SetNumberOfScalarComponents(1)

    extent = importer.GetDataExtent()

    importer.SetDataExtent(extent[0], extent[0] + dim[2] - 1,
                           extent[2], extent[2] + dim[1] - 1,
                           extent[4], extent[4] + dim[0] - 1)

    importer.SetWholeExtent(extent[0], extent[0] + dim[2] - 1,
                            extent[2], extent[2] + dim[1] - 1,
                            extent[4], extent[4] + dim[0] - 1)

    importer.SetDataSpacing(spacing[0], spacing[1], spacing[2])
    importer.SetDataOrigin(origin[0], origin[0], origin[2])

    image = importer.GetOutput()
    image.Update()
    return image


def numpy_to_vtk(array, spacing=(1., 1., 1.)):
    """Convert numpy array to vtkImageData.
    Args:
        array (~numpy.ndarray)  : Numpy array in XYZ format with any dtype.
        spacing (tuple of float): Spacing for X, Y and Z respectively.
    Returns:
        ret (vtk.vtkImageData)  : 3D vtkImageData in XYZ format
    """
    dim = array.shape

    # Transpose array to ZYX format to get string representation
    array_string = array.transpose(2, 1, 0).astype(np.float32).tostring()
    importer = vtk.vtkImageImport()
    importer.CopyImportVoidPointer(array_string, len(array_string))
    importer.SetDataScalarType(vtk.VTK_FLOAT)
    importer.SetNumberOfScalarComponents(1)
    extent = importer.GetDataExtent()

    importer.SetDataExtent(extent[0], extent[0] + dim[0] - 1,
                           extent[2], extent[2] + dim[1] - 1,
                           extent[4], extent[4] + dim[2] - 1)

    importer.SetWholeExtent(extent[0], extent[0] + dim[0] - 1,
                            extent[2], extent[2] + dim[1] - 1,
                            extent[4], extent[4] + dim[2] - 1)

    importer.SetDataSpacing(spacing[0], spacing[1], spacing[2])
    importer.SetDataOrigin(0, 0, 0)

    importer.Update()
    image_data = importer.GetOutput()

    ret = vtk.vtkImageData()
    ret.DeepCopy(image_data)
    return ret


def vtk_to_numpy(image):
    """Converts vtkImageData to numpy.ndarray.

        Args:
            image: 3D vtkImageData.

        Returns:
            array: 3D numpy.array.
    """
    dims = image.GetDimensions()
    points_data = image.GetPointData().GetScalars()

    array = numpy_support.vtk_to_numpy(points_data)
    array = array.reshape(dims[2], dims[1], dims[0])
    array = array.transpose(2, 1, 0)
    return array
