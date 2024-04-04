import vtk
from vtk.util import numpy_support
import numpy as np


ACTIVE_OPACITY = 0.6


def make_line(point_list, close):
    """Makes line from list of points.

    Args:
        point_list: list of points (numpy.ndarray is also compatible).
        close: closing flag.

    Returns:
        line: vtkPolyData.
    """
    points = vtk.vtkPoints()
    points.SetNumberOfPoints(len(point_list))
    lines = vtk.vtkCellArray()

    if close:
        lines.InsertNextCell(len(point_list) + 1)
    else:
        lines.InsertNextCell(len(point_list))

    for i, point in enumerate(point_list):
        points.SetPoint(i, point[0], point[1], point[2])
        lines.InsertCellPoint(i)

    if close:
        lines.InsertCellPoint(0)

    line = vtk.vtkPolyData()
    line.SetPoints(points)
    line.SetLines(lines)
    return line


def make_rectangle(start_point, end_point):
    """Makes a rectangle.

    Args:
        start_point (np.ndarray): start point for drawing.
        end_point (np.ndarray): end point for drawing.

    Returns:
        rectangle (vtkPolyData): polydata of rectangle.
    """
    points = vtk.vtkPoints()
    points.SetNumberOfPoints(4)
    points.SetPoint(0, start_point[0], start_point[1], start_point[2])
    points.SetPoint(1, end_point[0], start_point[1], start_point[2])
    points.SetPoint(2, end_point[0], end_point[1], start_point[2])
    points.SetPoint(3, start_point[0], end_point[1], start_point[2])

    lines = vtk.vtkCellArray()
    lines.InsertNextCell(5)
    for i in range(4):
        lines.InsertCellPoint(i)
    lines.InsertCellPoint(0)

    rectangle = vtk.vtkPolyData()
    rectangle.SetPoints(points)
    rectangle.SetLines(lines)
    return rectangle


def polydata_to_point_list(polydata):
    """Converts polydata to list of points.

    Args:
        polydata: vtkPolyData.

    Returns:
        point_list: list of points.
    """
    point_list = []
    for i in range(polydata.GetNumberOfPoints()):
        point_list.append(polydata.GetPoints().GetPoint(i))
    return point_list


def polydata_to_numpy(polydata):
    """Converts polydata to numpy.ndarray.

    Args:
        polydata: vtkPolyData.

    Returns:
        stack: numpy.ndarray.
    """
    stack = None
    for i in range(polydata.GetNumberOfPoints()):
        point = polydata.GetPoints().GetPoint(i)
        if stack is None:
            stack = np.array(point)
        else:
            stack = np.vstack((stack, point))
    return stack


def numpy_to_polydata(verts):
    """Converts numpy.ndarray to polydata

    Args:
        verts (ndarray)

    Returns:
        polydata (vtk.vtkPolyData)
    """
    polydata = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    points.SetData(numpy_support.numpy_to_vtk(verts))
    polydata.SetPoints(points)
    return polydata


def make_actor(polydata, color=None, width=None, opacity=ACTIVE_OPACITY, fill_inside=True):
    """Makes actor of polydata.

    Args:
        polydata: vtkPolyData.

    Returns:
        actor: vtkActor.
    """
    if fill_inside:
        tri = vtk.vtkContourTriangulator()
        tri.SetInputData(polydata)
        tri.Update()
        polydata = tri.GetOutput()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polydata)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    if color is not None:
        actor.GetProperty().SetColor(color)

    if width is not None:
        actor.GetProperty().SetLineWidth(width)
    else:
        actor.GetProperty().SetLineWidth(10.0)

    if opacity is not None:
        actor.GetProperty().SetOpacity(opacity)

    return actor


def show_polydata(polydata):
    """Show polydata.

    Args:
        polydata: vtkPolyData.
    """
    actor = make_actor(polydata)

    ren = vtk.vtkRenderer()
    renwin = vtk.vtkRenderWindow()
    iren = vtk.vtkRenderWindowInteractor()
    renwin.AddRenderer(ren)
    iren.SetRenderWindow(renwin)

    ren.AddActor(actor)

    renwin.Render()
    iren.Start()


def make_caption_actor(point, text, color=None, size=None, opacity=None):
    """Makes actor of caption.

    Args:
        point: text location.
        text: output text

    Returns:
        actor: vtkActor.
    """
    actor = vtk.vtkCaptionActor2D()
    actor.SetAttachmentPoint(point)
    actor.SetCaption(text)
    actor.BorderOff()
    # actor.ThreeDimensionalLeaderOff()
    actor.GetTextActor().SetTextScaleModeToNone()
    prop = actor.GetCaptionTextProperty()
    # prop.BoldOff()
    prop.ItalicOff()
    prop.ShadowOff()

    if color is not None:
        actor.GetProperty().SetColor(color)
        prop.SetColor(color)

    if size is not None:
        prop.SetFontSize(size)

    if opacity is not None:
        prop.SetOpacity(opacity)

    return actor


def make_text_actor(point, text, color=None, size=None, opacity=None, align=None):
    """Makes actor of text.

    Args:
        point: text location.
        text: output text

    Returns:
        actor: vtkActor.
    """
    actor = vtk.vtkTextActor()
    actor.SetPosition2(point)
    actor.SetInput(text)
    prop = actor.GetTextProperty()

    if color is not None:
        prop.SetColor(color)

    if size is not None:
        prop.SetFontSize(size)

    if opacity is not None:
        prop.SetOpacity(opacity)

    if align is not None:
        if align == 0:
            prop.SetJustificationToLeft()
            prop.SetVerticalJustificationToBottom()
        elif align == 1:
            prop.SetJustificationToCentered()
            prop.SetVerticalJustificationToBottom()
        elif align == 2:
            prop.SetJustificationToRight()
            prop.SetVerticalJustificationToBottom()
        elif align == 3:
            prop.SetJustificationToLeft()
            prop.SetVerticalJustificationToCentered()
        elif align == 4:
            prop.SetJustificationToCentered()
            prop.SetVerticalJustificationToCentered()
        elif align == 5:
            prop.SetJustificationToRight()
            prop.SetVerticalJustificationToCentered()
        elif align == 6:
            prop.SetJustificationToLeft()
            prop.SetVerticalJustificationToTop()
        elif align == 7:
            prop.SetJustificationToCentered()
            prop.SetVerticalJustificationToTop()
        elif align == 8:
            prop.SetJustificationToRight()
            prop.SetVerticalJustificationToTop()

    return actor


def get_axial_bound_area(polydata):
    """Calculates bound area on an axial plane.

    Args:
        polydata: vtkPolyData.

    Returns:
        area: calculated area.
    """
    bounds = polydata.GetBounds()
    area = (bounds[1] - bounds[0]) * (bounds[3] - bounds[2])
    return area


def get_center_of_mass(polydata):
    """Gets center of mass.

    Args:
        polydata: vtkPolyData.

    Returns:
        center: center of mass of the polydata.
    """
    com = vtk.vtkCenterOfMass()
    com.SetInput(polydata)
    com.SetUseScalarsAsWeights(False)
    com.Update()
    center = com.GetCenter()
    return center


def translate_polydata(polydata, dx, dy, dz):
    """Translates the location of polydata.

    Args:
        polydata: vtkPolyData.
        dx: distance along x-axis.
        dy: distance along y-axis.
        dz: distance along z-axis.
    """
    translate = vtk.vtkTransform()
    translate.Translate(dx, dy, dz)
    tf = vtk.vtkTransformPolyDataFilter()
    tf.SetInputData(polydata)
    tf.SetTransform(translate)
    tf.Update()
    polydata = tf.GetOutput()
    return polydata
