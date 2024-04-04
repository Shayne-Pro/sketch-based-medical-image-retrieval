import vtk
from collections import defaultdict
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QScrollBar
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QDockWidget
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from .viewer_widget import ViewerWidget
from .vtk_module.utils import make_text_actor
from .vtk_module import ViewerController
from .utils.state import StateBase
from .utils.io import read_niigz
from .utils.image import calc_window_width_level

from .utils import font
from .utils import font_semibold


BRUSH = 'BRUSH'
LINE = 'LINE'
DRAWING = 'DRAWING'
START = 'START'
END = 'END'


def style_highlight():
    return str("""
        QDockWidget > QWidget {
            border: 4px solid #3dc1d3;
        }
    """)


def style_normal():
    return str("""
        QDockWidget > QWidget {
            border: 0px solid #3dc1d3;
        }
    """)


class QueryWidget(ViewerWidget):

    def __init__(self, main_widget, app_controller):
        self.gl_config = app_controller.gl_config

        super().__init__(main_widget, app_controller)

        self.setWindowTitle('Query')
        self.setFloating(False)

    def closeEvent(self, event):
        event.ignore()

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
        self.toggle_sketching_action = QAction(
            QIcon(self.gl_config['static']['glass_icon']), '&SketchOnImage', self)
        self.toggle_sketching_action.setStatusTip('Sketch on the image')
        self.toggle_sketching_action.setCheckable(True)
        self.toggle_sketching_action.triggered.connect(
            lambda: self.toggle_sketching(
                self.toggle_sketching_action.isChecked())
        )

        self.use_brush_action = QAction(
            QIcon(self.gl_config['static']['brush_icon']), '&Brush', self)
        self.use_brush_action.setStatusTip('Use Bruch')
        self.use_brush_action.setCheckable(False)
        self.use_brush_action.triggered.connect(
            lambda: self.use_brush(self.use_brush_action.isChecked())
        )

        self.use_pen_action = QAction(
            QIcon(self.gl_config['static']['pencil_icon']), '&Pen', self)
        self.use_pen_action.setStatusTip('Use Pen')
        self.use_pen_action.setCheckable(False)
        self.use_pen_action.triggered.connect(
            lambda: self.use_pen(self.use_pen_action.isChecked())
        )

        self.use_measure_action = QAction(
            QIcon(self.gl_config['static']['scale_icon']), '&Calculate distance', self)
        self.use_measure_action.setStatusTip('Calculate distance')
        self.use_measure_action.setCheckable(False)
        self.use_measure_action.triggered.connect(
            lambda: self.use_measure(self.use_measure_action.isChecked())
        )

        self.add_contour_action = QAction(
            QIcon(self.gl_config['static']['duplicate_icon']), '&AddContour', self)
        self.add_contour_action.setStatusTip('Add New Contour')
        self.add_contour_action.triggered.connect(self.add_contour)

        self.remove_contour_action = QAction(
            QIcon(self.gl_config['static']['remove_icon']), '&RemoveContour', self)
        self.remove_contour_action.setStatusTip('Remove Current Contour')
        self.remove_contour_action.triggered.connect(self.remove_contour)

        self.change_contour_action = QAction(
            QIcon(self.gl_config['static']['exchange_icon']), '&ChangeContour', self)
        self.change_contour_action.setStatusTip('Change Current Contour')
        self.change_contour_action.triggered.connect(self.change_contour)

        # font = QFont()
        # font.setFamily("Segoe UI")

        self.structure_select = QComboBox()
        self.structure_select.setFont(font)
        self.structure_select.setFixedWidth(400)
        self.structure_select.setEnabled(False)

        self.search_button = QPushButton('Search', self)
        self.search_button.setFont(font_semibold)
        self.search_button.setEnabled(False)
        self.search_button.clicked.connect(self.app_controller.search_images)

        self.tool_bar = QToolBar()
        self.tool_bar.addAction(self.toggle_sketching_action)
        self.tool_bar.addSeparator()
        self.tool_bar.addWidget(self.structure_select)
        self.tool_bar.addSeparator()
        self.tool_bar.addAction(self.use_brush_action)
        self.tool_bar.addAction(self.use_pen_action)
        self.tool_bar.addSeparator()
        self.tool_bar.addAction(self.add_contour_action)
        self.tool_bar.addAction(self.remove_contour_action)
        self.tool_bar.addAction(self.change_contour_action)
        self.tool_bar.addSeparator()
        self.tool_bar.addAction(self.use_measure_action)
        self.tool_bar.addSeparator()
        self.tool_bar.addWidget(self.search_button)

    def toggle_sketching(self, is_checked):
        if is_checked:
            self.app_controller.init_structure_list()
            self.start_sketching()

        else:
            self.stop_sketching()

    def use_brush(self, is_checked):
        self.toggle_brush_action(is_checked)

        if is_checked:
            self.viewer_controller.state['drawing_mode'] = BRUSH

        else:
            self.viewer_controller.state['drawing_mode'] = None

    def use_pen(self, is_checked):
        self.toggle_pen_action(is_checked)

        if is_checked:
            self.viewer_controller.state['drawing_mode'] = LINE

        else:
            self.viewer_controller.state['drawing_mode'] = None

    def use_measure(self, is_checked):
        is_editable = self.viewer_controller.state['is_editable']

        if is_checked and is_editable:
            self.viewer_controller.start_measure()

        else:
            if is_editable:
                self.viewer_controller.stop_measure()

    def toggle_brush_action(self, is_checked):
        if is_checked:
            self.use_pen_action.setChecked(False)

    def toggle_pen_action(self, is_checked):
        if is_checked:
            self.use_brush_action.setChecked(False)

    def add_contour(self):
        self.viewer_controller.add_active_contour()

    def remove_contour(self):
        self.viewer_controller.delete_active_contour()
        self.viewer_controller.state['is_edited'] = True

    def change_contour(self):
        self.viewer_controller.change_active_contour_to_next()

    def init_viewer(self, image_path, window_width=None, window_center=None):
        dataset_type = self.app_controller.app_state['dataset_type']
        self.image = read_niigz(image_path, dataset_type=dataset_type)

        self.viewer = vtk.vtkImageViewer2()
        self.viewer.SetInputData(self.image)

        self.min_slice = self.viewer.GetSliceMin()
        self.max_slice = self.viewer.GetSliceMax()

        self.istyle = vtk.vtkInteractorStyleImage()
        self.iren.SetInteractorStyle(self.istyle)

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
        )

        if not (window_width and window_center):
            window_width, window_center = calc_window_width_level(self.image)

        self.viewer_controller.update_image_window(
            window_width=window_width,
            window_center=window_center,
        )

    def start_viewer(self):
        for structure in self.app_controller.app_state['structure_list']:
            self.structure_select.addItem(structure.class_name)

        self.structure_select.activated.connect(
            lambda: self.structure_list_changed(
                self.structure_select.currentIndex())
        )

        self.scroll.valueChanged.connect(self.scroll_value_changed)
        self.scroll.setMinimum(self.min_slice)
        self.scroll.setMaximum(self.max_slice)
        self.scroll.setValue(self.min_slice)

        state = self.viewer_controller.state
        controller = self.viewer_controller

        def wheel_forward_event(caller, event):
            if state['is_editable']:
                if state['is_drawing'] and state['drawing_mode'] == BRUSH:
                    controller.increase_brush_size()

            else:
                if state['slice'] > state['min_slice']:
                    state['slice'] -= 1
                    self.scroll.setValue(state['slice'])

        def wheel_backward_event(caller, event):
            if state['is_editable']:
                if state['is_drawing'] and state['drawing_mode'] == BRUSH:
                    controller.decrease_brush_size()

            else:
                if state['slice'] < state['max_slice']:
                    state['slice'] += 1
                    self.scroll.setValue(state['slice'])

        def on_leave(caller, event):
            if state['is_editable']:
                controller.refresh()

        def on_enter(caller, event):
            if state['is_editable']:
                controller.refresh()

        def button_event(caller, event):
            if state['is_calc_dist']:
                if event == 'LeftButtonPressEvent':
                    self.viewer_controller.draw_dist_line(START)

                elif event == 'LeftButtonReleaseEvent':
                    self.viewer_controller.draw_dist_line(END)

            elif state['is_editable']:
                if event == 'LeftButtonPressEvent':
                    state['is_drawing'] = True

                    if state['drawing_mode'] == BRUSH:
                        controller.process_draw_brush()

                elif event == 'LeftButtonReleaseEvent':
                    if state['drawing_mode'] == LINE:
                        controller.draw_line(finalize=True)

                    elif state['drawing_mode'] == BRUSH:
                        controller.end_draw_brush()

                    state['is_edited'] = True
                    state['is_drawing'] = False

        def register_button_event():
            if not state['istyle'].HasObserver('LeftButtonPressEvent'):
                state['istyle'].AddObserver(
                    'LeftButtonPressEvent', button_event
                )

            if not state['istyle'].HasObserver('LeftButtonReleaseEvent'):
                state['istyle'].AddObserver(
                    'LeftButtonReleaseEvent', button_event
                )

        def unregister_button_event():
            if state['istyle'].HasObserver('LeftButtonPressEvent'):
                state['istyle'] = None
                self.istyle = vtk.vtkInteractorStyleImage()

                self.istyle.AddObserver(
                    'MouseWheelForwardEvent', wheel_forward_event
                )
                self.istyle.AddObserver(
                    'MouseWheelBackwardEvent', wheel_backward_event
                )

                state['iren'].SetInteractorStyle(self.istyle)
                state['istyle'] = self.istyle

        def mouse_move(caller, event):
            if not state['is_editable']:
                unregister_button_event()
                return

            if state['drawing_mode'] is None and not state['is_calc_dist']:
                unregister_button_event()

            else:
                register_button_event()
                if state['is_drawing']:
                    if state['drawing_mode'] == LINE:
                        controller.draw_line(finalize=False)

                    elif state['drawing_mode'] == BRUSH:
                        controller.process_draw_brush()

                elif state['is_calc_dist']:
                    controller.draw_dist_line(DRAWING)

        def key_press(caller, event):
            key = caller.GetKeySym()

            if state['is_drawing']:
                return

            if state['is_editable']:
                if key in ['d']:
                    controller.remove_contour_in_slice()
                    state['is_edited'] = True

                elif key in ['c']:
                    controller.change_active_contour_to_next()

                elif key in ['s']:
                    struct_idx, contour_idx = controller.get_structure_on_mouse()

                    if struct_idx is not None:
                        if struct_idx == controller.state['structure_idx']:
                            controller.change_active_contour(contour_idx)

                        else:
                            self.change_structure(struct_idx)
                            controller.change_active_contour(contour_idx)

                elif key in ['n']:
                    next_idx = controller.get_next_structure_idx()
                    self.change_structure(next_idx)

        self.istyle.AddObserver('MouseWheelForwardEvent', wheel_forward_event)
        self.istyle.AddObserver(
            'MouseWheelBackwardEvent', wheel_backward_event)
        self.istyle.AddObserver('LeaveEvent', on_leave)
        self.istyle.AddObserver('EnterEvent', on_enter)
        self.iren.AddObserver("MouseMoveEvent", mouse_move)
        self.iren.AddObserver("KeyPressEvent", key_press)

        self.viewer.SetRenderWindow(self.iren.GetRenderWindow())
        self.viewer.GetRenderer().GetActiveCamera().ParallelProjectionOn()
        self.viewer.Render()

    def structure_list_changed(self, current_index):
        self.app_controller.app_state['structure_idx'] = current_index
        self.viewer_controller.change_active_structure(current_index)

    def change_structure(self, next_index):
        self.structure_select.setCurrentIndex(next_index)
        self.viewer_controller.change_active_structure(next_index)

    def start_sketching(self):
        self.use_brush_action.setCheckable(True)
        self.use_pen_action.setCheckable(True)
        self.use_measure_action.setCheckable(True)
        self.structure_select.setEnabled(True)
        self.search_button.setEnabled(True)

        self.viewer_controller.activate_editing(
            is_drawing=False,
            is_edited=False,
            drawing_mode=None,
            brush_size=3.0,
            max_brush_size=50,
            min_brush_size=0.1,
            tolerance_area=0.1,
            structure_list=self.app_controller.app_state['structure_list'],
            structure_idx=self.app_controller.app_state['structure_idx'],
        )

        self.setStyleSheet(style_highlight())

    def stop_sketching(self):
        self.toggle_sketching_action.setChecked(False)
        self.use_brush_action.setCheckable(False)
        self.use_pen_action.setCheckable(False)
        self.use_measure_action.setCheckable(False)
        self.structure_select.setEnabled(False)
        self.search_button.setEnabled(False)

        self.viewer_controller.inactivate_editing()
        self.setStyleSheet(style_normal())

    def scroll_value_changed(self, idx):
        if not self.viewer_controller.state['is_editable']:
            if self.min_slice <= idx and idx <= self.max_slice:
                self.viewer.SetSlice(idx)
                self.viewer.Render()
                self.viewer_controller.state['slice'] = idx

        else:
            self.scroll.setValue(self.viewer_controller.state['slice'])
