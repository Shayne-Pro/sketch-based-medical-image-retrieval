import vtk
from operator import itemgetter

from .io import numpy_to_vtk


def get_number_of_regions(polydata):
    """Get number of unconnected regions.

    Args:
        polydata: vtkPolyData.
    Returns:
        num_regions: number of unconnected regions extracted from polydata.
    """
    extractor = vtk.vtkPolyDataConnectivityFilter()
    extractor.SetInputData(polydata)
    extractor.Update()
    num_regions = extractor.GetNumberOfExtractedRegions()

    return num_regions


def get_topk_volumes(polydata, k):
    """Get top-k largest regions from polydata.

    Args:
        polydata: vtkPolyData.
        k: number of regions to be extracted.
    Returns:
        regions: list of extracted regions as vtkPolyData.
    """

    num_regions = get_number_of_regions(polydata)

    masses = []
    for i in range(num_regions):
        extractor = vtk.vtkPolyDataConnectivityFilter()
        extractor.SetInputData(polydata)
        extractor.SetExtractionModeToSpecifiedRegions()
        extractor.AddSpecifiedRegion(i)
        extractor.Update()

        region = extractor.GetOutput()

        mass = vtk.vtkMassProperties()
        mass.SetInputData(region)
        mass.Update()
        masses.append([i, mass.GetVolume()])

    masses = list(reversed(sorted(masses, key=itemgetter(1))))[:k]

    regions = []
    for mass in masses:
        extractor = vtk.vtkPolyDataConnectivityFilter()
        extractor.SetInputData(polydata)
        extractor.SetExtractionModeToSpecifiedRegions()
        extractor.AddSpecifiedRegion(mass[0])
        extractor.Update()
        regions.append(extractor.GetOutput())

    return regions


def get_volume_from_numpy(label, threshold=100):
    """Get volume from numpy array by using vtkImageMarchingCubes.

    Args:
        label: numpy 3d-array.
        threshold: threshold value used by vtkImageMarchingCubes.
    Returns:
        polydata: extracted vtkPolyData.
    """
    volume = numpy_to_vtk(label)
    marcher = vtk.vtkImageMarchingCubes()
    marcher.SetInputData(volume)
    marcher.SetValue(0, threshold)
    marcher.Update()
    polydata = marcher.GetOutput()

    return polydata
