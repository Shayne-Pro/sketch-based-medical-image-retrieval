import traceback
from collections import defaultdict
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QThread
from PyQt5.QtCore import QSize
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QScrollBar
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QToolBar

from .vtk_module.utils import make_text_actor
from .vtk_module import ViewerController
from .utils.state import StateBase
from .utils.io import read_niigz
from .utils.hl_scrollbar import HLScrollBar
from .utils.image import calc_window_width_level


assert vtk.vtkVersion().GetVTKVersion() == '8.1.2'


BRUSH = 'BRUSH'
LINE = 'LINE'
DRAWING = 'DRAWING'
START = 'START'
END = 'END'


def style_highlight():
    return str("""
        QDockWidget > QWidget {
            border: 12px solid #3dc1d3;
        }
    """)


def style_normal():
    return str("""
        QDockWidget > QWidget {
            border: 0px solid #3dc1d3;
        }
    """)


class ReadImageWorker(QThread):
    finished = pyqtSignal(object)

    def __init__(self, image_path, dataset_type):
        super().__init__()
        self.image_path = image_path
        self.dataset_type = dataset_type

    def run(self):
        image = read_niigz(self.image_path, dataset_type=self.dataset_type)
        self.finished.emit(image)


class ViewerWidget(QDockWidget):

    def __init__(self, main_widget, app_controller, window_width=None, window_center=None):
        super().__init__()

        self.main_widget = main_widget
        self.app_controller = app_controller
        self.current_slice = 0
        self.window_width = window_width
        self.window_center = window_center

        self.setMinimumSize(QSize(1200, 1200))
        self.init_layout()
        self.setWindowTitle('Viewer')

    def init_layout(self):
        self.init_tool_bar()

        self.iren = QVTKRenderWindowInteractor(self)
        render_window = self.iren.GetRenderWindow()
        render_window.SetOffScreenRendering(False)
        self.iren.Initialize()
        self.iren.Start()

        self.scroll = QScrollBar()

        self.layout = QGridLayout()
        self.layout.addWidget(self.iren, 0, 0, 1, 1)
        self.layout.addWidget(self.scroll, 0, 1, 1, 1)

        self.layout_2 = QVBoxLayout()
        self.layout_2.addWidget(self.tool_bar)
        self.layout_2.addLayout(self.layout)

        docked = QDockWidget()
        dockedWidget = QWidget()
        docked.setWidget(dockedWidget)
        dockedWidget.setLayout(self.layout_2)

        self.setWidget(dockedWidget)

    def init_tool_bar(self):
        self.use_measure_action = QAction(
            QIcon('app/static/icon/scale.png'), '&Calculate distance', self)
        self.use_measure_action.setStatusTip('Calculate distance')
        self.use_measure_action.setCheckable(True)
        self.use_measure_action.triggered.connect(
            lambda: self.use_measure(self.use_measure_action.isChecked())
        )

        self.tool_bar = QToolBar()
        self.tool_bar.addAction(self.use_measure_action)

    def use_measure(self, is_checked):
        if is_checked:
            self.viewer_controller.start_measure()

            self.istyle.AddObserver(
                'LeftButtonPressEvent', self.button_event
            )

            self.istyle.AddObserver(
                'LeftButtonReleaseEvent', self.button_event
            )

        else:
            self.viewer_controller.stop_measure()

            self.istyle = None
            self.istyle = vtk.vtkInteractorStyleImage()

            self.istyle.AddObserver(
                'MouseWheelForwardEvent', self.wheel_forward_event
            )
            self.istyle.AddObserver(
                'MouseWheelBackwardEvent', self.wheel_backward_event
            )

            self.viewer_controller.state['iren'].SetInteractorStyle(self.istyle)
            self.viewer_controller.state['istyle'] = self.istyle

    def button_event(self, caller, event):
        if self.viewer_controller.state['is_calc_dist']:
            if event == 'LeftButtonPressEvent':
                self.viewer_controller.draw_dist_line(START)

            elif event == 'LeftButtonReleaseEvent':
                self.viewer_controller.draw_dist_line(END)

    def wheel_forward_event(self, caller, event):
        if self.current_slice > self.min_slice:
            self.current_slice -= 1
            self.scroll.setValue(self.current_slice)

    def wheel_backward_event(self, caller, event):
        if self.current_slice < self.max_slice:
            self.current_slice += 1
            self.scroll.setValue(self.current_slice)

    def init_viewer(self, patient_id, image_path, viewer_title=None, selected_slice=None):
        self.selected_slice = selected_slice

        if viewer_title is None:
            self.setWindowTitle(patient_id)

        else:
            self.setWindowTitle(viewer_title)

        self.worker = ReadImageWorker(
            image_path, self.app_controller.app_state['dataset_type']
        )
        self.worker.finished.connect(self._start_viewer)
        self.worker.start()

    def get_z_length(self):
        _, _, _, _, z_min, z_max = self.image.GetExtent()
        return z_max - z_min + 1

    def get_image_origin(self):
        return self.image.GetOrigin()

    def get_image_spacing(self):
        return self.image.GetSpacing()

    def get_axial_extent(self):
        x_min, x_max, y_min, y_max, _, _ = self.image.GetExtent()
        return (x_max - x_min + 1, y_max - y_min + 1)

    def _start_viewer(self, image):
        self.viewer = vtk.vtkImageViewer2()
        self.viewer.SetInputData(image)
        self.image = image

        self.min_slice = self.viewer.GetSliceMin()
        self.max_slice = self.viewer.GetSliceMax()

        self.scroll.valueChanged.connect(self.scroll_value_changed)

        self.istyle = vtk.vtkInteractorStyleImage()
        self.iren.SetInteractorStyle(self.istyle)

        self.info_text = make_text_actor(
            (0, 0),
            'Slice {} / {}'.format(self.max_slice, self.max_slice),
            align=0,
            size=20,
            color=vtk.vtkNamedColors().GetColor3d("White")
        )
        self.viewer.GetRenderer().AddActor2D(self.info_text)

        self.viewer_controller = ViewerController(
            is_editable=False,                    # アノテーション可能かどうか
            is_calc_dist=False,                   # 距離計算状態かどうか
            slice=self.min_slice,                 # 現在のスライス
            min_slice=self.min_slice,             # 最小のスライス番号
            max_slice=self.max_slice,             # 最大のスライス番号
            slice_locations=defaultdict(int),     # スライス番号とZ座標の対応表
            iren=self.iren,                       # irenインスタンス
            istyle=self.istyle,                   # istyleインスタンス
            viewer=self.viewer,                   # viewerインスタンス
            info_text=self.info_text,             # textインスタンス
        )

        self.scroll.setMinimum(self.min_slice)
        self.scroll.setMaximum(self.max_slice)
        self.scroll.setValue(self.current_slice)

        state = self.viewer_controller.state
        controller = self.viewer_controller

        def mouse_move(caller, event):
            if state['is_calc_dist']:
                controller.draw_dist_line(DRAWING)

        self.istyle.AddObserver('MouseWheelForwardEvent', self.wheel_forward_event)
        self.istyle.AddObserver('MouseWheelBackwardEvent', self.wheel_backward_event)
        self.iren.AddObserver("MouseMoveEvent", mouse_move)

        if not (self.window_width and self.window_center):
            self.window_width, self.window_center = calc_window_width_level(self.image)

        self.viewer.SetColorWindow(self.window_width)
        self.viewer.SetColorLevel(self.window_center)

        self.viewer.SetRenderWindow(self.iren.GetRenderWindow())
        self.viewer.GetRenderer().GetActiveCamera().ParallelProjectionOn()
        self.viewer.Render()

        if self.selected_slice:
            self.current_slice = self.max_slice - self.selected_slice
            self.scroll_value_changed(self.current_slice)
            self.scroll.setValue(self.current_slice)

    def scroll_value_changed(self, idx):
        if self.min_slice <= idx and idx <= self.max_slice:
            self.viewer.SetSlice(idx)

            self.viewer.GetRenderer().RemoveActor(self.info_text)
            self.info_text = make_text_actor(
                (0, 0),
                'Slice {} / {}'.format(self.max_slice - idx, self.max_slice),
                align=0,
                size=20,
                color=vtk.vtkNamedColors().GetColor3d("White")
            )
            self.viewer.GetRenderer().AddActor2D(self.info_text)

            if self.selected_slice:
                if self.max_slice - idx == self.selected_slice:
                    self.setStyleSheet(style_highlight())
                else:
                    self.setStyleSheet(style_normal())

            self.viewer.Render()

            self.current_slice = idx
