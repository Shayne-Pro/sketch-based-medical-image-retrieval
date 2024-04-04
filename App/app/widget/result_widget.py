import os
from datetime import datetime
import copy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backend_bases import MouseButton

from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QCheckBox
from torch import is_same_size

from .utils import font
from .utils import font_semibold


LABEL_PREFIX = ['seg', 'lbl']
LABEL_VMIN = 0
LABEL_VMAX = 3
TOPK_PATIENT_TO_SHOW = 5

Accepted = 'Accepted'
Rejected = 'Rejected'
Unselected = 'Unselected'

MICCAI_BraTS = 'MICCAI_BraTS'
MICCAI_BraTS_EVAL_POINTS = ['Size', 'Location', 'Pattern of CE']

TEMP_DIR_PATH = './results/temp'

DPI = 512


def accept_highlight():
    return str("""
        QCheckBox {
            color: #0000FF;
        }
    """)


def reject_highlight():
    return str("""
        QCheckBox {
            color: #FF0000;
        }
    """)


class CheckBoxWithState(QCheckBox):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_selected = False
        self.setStyleSheet(reject_highlight())
        self.stateChanged.connect(self.state_changed)

    def state_changed(self):
        if self.isChecked():
            self.is_selected = True
            self.setStyleSheet(accept_highlight())
        else:
            self.is_selected = False
            self.setStyleSheet(reject_highlight())

    def freeze(self):
        self.setEnabled(False)

    def result(self):
        return self.is_selected


class ResultContent(QWidget):

    def __init__(self, app_controller, retrieved_num, retrieved_image, record, vmin=None, vmax=None, is_same_patient=False):
        super().__init__()

        self.app_controller = app_controller
        self.retrieved_num = retrieved_num
        self.retrieved_image = retrieved_image
        self.patient_id = self.retrieved_image[0]['patient_id']
        self.slice_num = self.retrieved_image[0]['slice_num']
        self.record = record
        self.is_same_patient = is_same_patient

        self.vmin = vmin
        self.vmax = vmax

        self.init_layout()

    def check_result(self):
        if self.app_controller.app_state['dataset_type'] == MICCAI_BraTS:
            true_ratio = self.checkBox_1.result() \
                + self.checkBox_2.result() \
                + self.checkBox_3.result()
            true_ratio /= 3.0

            return {
                'retrieved_num': self.retrieved_num,
                'patient_id': self.patient_id,
                'slice_num': self.slice_num,
                'eval_point_1': self.checkBox_1.result(),
                'eval_point_2': self.checkBox_2.result(),
                'eval_point_3': self.checkBox_3.result(),
                'true_ratio': true_ratio,
                'is_same_patient': self.is_same_patient,
            }

        else:
            raise NotImplementedError(
                'Only the MICCAI BraTS 2019 dataset is available in the public version.')

    def canvas_clicked(self, event):
        if event.dblclick:
            self.app_controller.show_image_in_viewer(self.record)

    def freeze_buttons(self):
        self.checkBox_1.freeze()
        self.checkBox_2.freeze()

        if self.app_controller.app_state['dataset_type'] == MICCAI_BraTS:
            self.checkBox_3.freeze()

    def init_layout(self):
        vLayout_1 = QVBoxLayout(self)

        subtitleLine = QLabel(self)
        subtitleLine.setFont(font)
        subtitleLine.setText('[No.{}] PatientID = {}, Slice = {}'.format(
            self.retrieved_num + 1, self.patient_id, self.slice_num)
        )
        vLayout_1.addWidget(subtitleLine)

        hLayout_1 = QHBoxLayout()
        vLayout_2 = QVBoxLayout()

        spacerItem_1 = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        vLayout_2.addItem(spacerItem_1)

        if self.app_controller.app_state['dataset_type'] == MICCAI_BraTS:
            self.checkBox_1 = CheckBoxWithState(
                MICCAI_BraTS_EVAL_POINTS[0], self)
            self.checkBox_2 = CheckBoxWithState(
                MICCAI_BraTS_EVAL_POINTS[1], self)
            self.checkBox_3 = CheckBoxWithState(
                MICCAI_BraTS_EVAL_POINTS[2], self)

            self.checkBox_1.setFont(font_semibold)
            self.checkBox_2.setFont(font_semibold)
            self.checkBox_3.setFont(font_semibold)

            vLayout_2.addWidget(self.checkBox_1)
            vLayout_2.addWidget(self.checkBox_2)
            vLayout_2.addWidget(self.checkBox_3)

        else:
            raise NotImplementedError(
                'Only the MICCAI BraTS 2019 dataset is available in the public version.')

        spacerItem_2 = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        vLayout_2.addItem(spacerItem_2)

        hLayout_1.addLayout(vLayout_2)

        fig = Figure()
        self.fc = FigureCanvas(fig)
        self.fc.mpl_connect("button_press_event", self.canvas_clicked)

        n_images = len(self.retrieved_image)

        for i, image in enumerate(self.retrieved_image):
            modality = image['modality']
            img = image['image']

            if modality in LABEL_PREFIX:
                cmap = 'jet'
                vmin = LABEL_VMIN
                vmax = LABEL_VMAX

            else:
                cmap = 'gray'

                if self.vmin:
                    vmin = self.vmin
                else:
                    vmin = img.min()

                if self.vmax:
                    vmax = self.vmax
                else:
                    vmax = img.max()

            self.fc.axes = fig.add_subplot(1, n_images, i + 1)
            self.fc.axes.axis('off')
            fig.tight_layout()

            if self.is_same_patient:
                fig.set_facecolor('orange')

            self.fc.axes.imshow(img, cmap=cmap, vmin=vmin, vmax=vmax)
            self.fc.axes.set_title(modality.upper())

        FigureCanvas.setSizePolicy(self.fc,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self.fc)

        hLayout_1.addWidget(self.fc)
        vLayout_1.addLayout(hLayout_1)


class ResultWidget(QDockWidget):

    def __init__(self, main_widget, app_controller, minimum_width, minimum_height):
        super().__init__()

        self.main_widget = main_widget
        self.app_controller = app_controller
        self.original_retrieved_records = None

        self.setMinimumSize(QSize(minimum_width, minimum_height))
        self.setWindowTitle('Retrieved results')
        self.setFloating(False)

    def set_ct_window(self, vmin, vmax):
        self.vmin = vmin
        self.vmax = vmax

    def closeEvent(self, event):
        event.ignore()

    def show_results(self, retrieved_images, retrieved_records):
        self.original_retrieved_records = copy.deepcopy(retrieved_records)

        retrieved_images = retrieved_images[:TOPK_PATIENT_TO_SHOW]

        self.content_list = []
        contents = QWidget()

        vLayout_1 = QVBoxLayout(contents)

        scrollArea = QScrollArea(self)
        scrollArea.setWidgetResizable(True)

        scrollAreaWidgetContents = QWidget()
        scrollAreaLayout = QVBoxLayout(scrollAreaWidgetContents)

        q_patient_id = self.app_controller.QuestionWidget.patient_id

        for i, retrieved_image in enumerate(retrieved_images):
            record = retrieved_records[i]

            is_same_patient = q_patient_id == record.patient_id

            content = ResultContent(
                self.app_controller, i, retrieved_image, record, self.vmin, self.vmax, is_same_patient
            )
            self.content_list.append(content)
            scrollAreaLayout.addWidget(content)

        scrollArea.setWidget(scrollAreaWidgetContents)
        vLayout_1.addWidget(scrollArea)

        hLayout_1 = QHBoxLayout(contents)

        spacerItem_1 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hLayout_1.addItem(spacerItem_1)

        self.summaryButton = QPushButton(contents)
        self.summaryButton.setFont(font_semibold)
        self.summaryButton.setText('Submit')
        self.summaryButton.clicked.connect(self.summarize_results)
        hLayout_1.addWidget(self.summaryButton)

        spacerItem_2 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hLayout_1.addItem(spacerItem_2)

        vLayout_1.addLayout(hLayout_1)

        self.setWidget(contents)

    def summarize_results(self):
        if not self.app_controller.QueryWidget.viewer_controller.state['is_editable']:
            QMessageBox.warning(
                self, 'WARNING', 'Query widget is not drawing mode.', QMessageBox.Yes)
            return None

        summary = []
        for content in self.content_list:
            result = content.check_result()
            summary.append(result)

        for content in self.content_list:
            content.freeze_buttons()

        for i, retrieved_record in enumerate(self.original_retrieved_records[TOPK_PATIENT_TO_SHOW:]):
            s = {
                'retrieved_num': i + TOPK_PATIENT_TO_SHOW,
                'patient_id': retrieved_record.patient_id,
                'slice_num': retrieved_record.slice_num,
                'eval_point_1': False,
                'eval_point_2': False,
                'true_ratio': 0.0,
                'is_same_patient': False,
            }

            if self.app_controller.app_state['dataset_type'] == MICCAI_BraTS:
                s.update({'eval_point3': False})

            summary.append(s)

        self.app_controller.next_page(summary)

    def clear(self):
        self.content_list = []
        contents = QWidget()
        vLayout_1 = QVBoxLayout(contents)
        self.setWidget(contents)


class DemoResultContent(QWidget):

    def __init__(self, app_controller, retrieved_num, retrieved_image, record, vmin=None, vmax=None):
        super().__init__()

        self.app_controller = app_controller
        self.retrieved_num = retrieved_num
        self.retrieved_image = retrieved_image
        self.patient_id = self.retrieved_image[0]['patient_id']
        self.slice_num = self.retrieved_image[0]['slice_num']
        self.record = record

        self.vmin = vmin
        self.vmax = vmax

        self.init_layout()

    def canvas_clicked(self, event):
        if event.dblclick:
            if event.button == MouseButton.LEFT:
                self.app_controller.show_image_in_viewer(self.record)

            elif event.button == MouseButton.RIGHT:
                self.save_selected_images()

    def save_selected_images(self):
        time_stamp = datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
        save_dir_path = os.path.join(TEMP_DIR_PATH, time_stamp)
        os.makedirs(save_dir_path, exist_ok=True)

        for image in self.retrieved_image:
            modality = image['modality']
            img = image['image']

            if modality in LABEL_PREFIX:
                cmap = 'jet'
                vmin = LABEL_VMIN
                vmax = LABEL_VMAX

            else:
                cmap = 'gray'

                if self.vmin:
                    vmin = self.vmin
                else:
                    vmin = img.min()

                if self.vmax:
                    vmax = self.vmax
                else:
                    vmax = img.max()

            file_name = self.patient_id + '_' + \
                str(self.slice_num).zfill(4) + '_' + modality
            save_path = os.path.join(save_dir_path, file_name + '.png')

            plt.imshow(img, cmap=cmap, vmin=vmin, vmax=vmax)
            plt.axis('off')
            plt.savefig(save_path, bbox_inches='tight', pad_inches=0, dpi=DPI)
            plt.clf()

    def init_layout(self):
        vLayout_1 = QVBoxLayout(self)

        subtitleLine = QLabel(self)
        subtitleLine.setFont(font)
        subtitleLine.setText('[No.{}] PatientID = {}, Slice = {}'.format(
            self.retrieved_num + 1, self.patient_id, self.slice_num)
        )
        vLayout_1.addWidget(subtitleLine)

        hLayout_1 = QHBoxLayout()

        fig = Figure()
        self.fc = FigureCanvas(fig)
        self.fc.mpl_connect("button_press_event", self.canvas_clicked)

        n_images = len(self.retrieved_image)

        for i, image in enumerate(self.retrieved_image):
            modality = image['modality']
            img = image['image']

            if modality in LABEL_PREFIX:
                cmap = 'jet'
                vmin = LABEL_VMIN
                vmax = LABEL_VMAX

            else:
                cmap = 'gray'

                if self.vmin:
                    vmin = self.vmin
                else:
                    vmin = img.min()

                if self.vmax:
                    vmax = self.vmax
                else:
                    vmax = img.max()

            self.fc.axes = fig.add_subplot(1, n_images, i + 1)
            self.fc.axes.axis('off')
            fig.tight_layout()
            self.fc.axes.imshow(img, cmap=cmap, vmin=vmin, vmax=vmax)
            self.fc.axes.set_title(modality.upper())

        FigureCanvas.setSizePolicy(self.fc,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self.fc)

        hLayout_1.addWidget(self.fc)
        vLayout_1.addLayout(hLayout_1)


class DemoResultWidget(QDockWidget):

    def __init__(self, main_widget, app_controller, minimum_width, minimum_height):
        super().__init__()

        self.main_widget = main_widget
        self.app_controller = app_controller
        self.original_retrieved_images = None

        self.setMinimumSize(QSize(minimum_width, minimum_height))
        self.setWindowTitle('Retrieved results')
        self.setFloating(False)

    def set_ct_window(self, vmin, vmax):
        self.vmin = vmin
        self.vmax = vmax

    def closeEvent(self, event):
        event.ignore()

    def show_results(self, retrieved_images, retrieved_records):
        self.original_retrieved_images = copy.deepcopy(retrieved_images)

        retrieved_images = retrieved_images[:TOPK_PATIENT_TO_SHOW]

        self.content_list = []
        contents = QWidget()

        vLayout_1 = QVBoxLayout(contents)

        scrollArea = QScrollArea(self)
        scrollArea.setWidgetResizable(True)

        scrollAreaWidgetContents = QWidget()
        scrollAreaLayout = QVBoxLayout(scrollAreaWidgetContents)

        for i, retrieved_image in enumerate(retrieved_images):
            record = retrieved_records[i]
            content = DemoResultContent(
                self.app_controller, i, retrieved_image, record, self.vmin, self.vmax
            )
            self.content_list.append(content)
            scrollAreaLayout.addWidget(content)

        scrollArea.setWidget(scrollAreaWidgetContents)
        vLayout_1.addWidget(scrollArea)

        self.setWidget(contents)
