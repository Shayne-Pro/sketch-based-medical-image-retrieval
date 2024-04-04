import itertools
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QWidget

from ..utils import load_config
from ..utils import normalize_image
from .utils import font
from .utils import font_semibold


LABEL_PREFIX = ['seg', 'lbl']
LABEL_VMIN = 0
LABEL_VMAX = 3

NO_HINT_LIMIT = 1


class QuestionGenerator(object):

    def __init__(self, question_config):
        self.question_config = question_config
        self.stage = None
        self.question = None

    def __next__(self):
        has_next = False

        if self.stage is None:
            self.stage = list(self.question_config.keys())[0]
            self.question = list(self.question_config[self.stage].keys())[0]
            has_next = True

        else:
            next_question = self.has_next_question()
            if next_question:
                self.question = next_question
                has_next = True

            else:
                next_stage = self.has_next_stage()
                if next_stage:
                    self.stage = next_stage
                    self.question = 'Question_1'
                    has_next = True

        if has_next:
            return self.stage, self.question

        else:
            raise StopIteration

    def has_next_stage(self):
        next_stage = 'STAGE_{}'.format(str(self.stage_num + 1))
        if next_stage in self.question_config.keys():
            return next_stage
        else:
            return None

    def has_next_question(self):
        next_question = 'Question_{}'.format(str(self.question_num + 1))
        if next_question in self.question_config[self.stage].keys():
            return next_question
        else:
            return None

    @property
    def stage_num(self):
        return int(self.stage.split('_')[1])

    @property
    def question_num(self):
        return int(self.question.split('_')[1])

    @property
    def n_questions(self):
        return len(list(self.question_config[self.stage].keys()))


class QuestionWidget(QDockWidget):

    def __init__(self, main_widget, app_controller):
        self.gl_config = app_controller.gl_config
        self.ds_config = app_controller.ds_config

        super().__init__()

        self.main_widget = main_widget
        self.app_controller = app_controller
        self.patient_id = None

        self.question_config = self.ds_config['questions']
        self.question_generator = QuestionGenerator(self.question_config)

        stage, question = next(self.question_generator)

        self.init_layout(stage, question)

        self.setWindowTitle('Question')
        self.setMinimumSize(
            QSize(self.gl_config['app']['question']['size'][0],
                  self.gl_config['app']['question']['size'][0]))
        self.setFloating(False)

    def closeEvent(self, event):
        event.ignore()

    def next(self):
        try:
            stage, question = next(self.question_generator)
            self.init_layout(stage, question)

            stage_num = int(stage.split('_')[1])
            question_num = int(question.split('_')[1])

            self.app_controller.app_state['stage'] = stage_num
            self.app_controller.app_state['question'] = question_num
            return True

        except StopIteration:
            return False

    def canvas_clicked(self, event):
        if event.dblclick:
            self.app_controller.show_image_in_viewer({
                'patient_id': self.config['patient_id'],
                'selected_slice': self.config['slice_num'],
            })

    def init_layout(self, stage, question):
        stage_num = int(stage.split('_')[1])
        question_num = int(question.split('_')[1])

        title_text = 'Stage {} ({}/{})'.format(
            stage_num,
            question_num,
            self.question_generator.n_questions,
        )

        self.config = self.question_config[stage][question]

        self.widget = QWidget(self)

        self.vLayout_1 = QVBoxLayout(self.widget)

        if self.config['type'] == 'text':
            spacerItem_1 = QSpacerItem(
                20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
            self.vLayout_1.addItem(spacerItem_1)

        self.groupBox = QGroupBox(self.widget)
        self.groupBox.setTitle(title_text)
        self.groupBox.setFont(font_semibold)
        self.vLayout_1.addWidget(self.groupBox)

        self.vLayout_2 = QVBoxLayout(self.groupBox)

        self.messageLabel = QLabel(self.groupBox)
        self.messageLabel.setWordWrap(True)
        self.messageLabel.setText(self.config['message'])
        self.messageLabel.setFont(font)
        self.vLayout_2.addWidget(self.messageLabel)

        if self.config['type'] == 'image':
            self.patient_id = self.config['patient_id']
            slice_num = self.config['slice_num']

            images = self.app_controller.get_image(self.patient_id, slice_num)
            n_images = len(images)

            fig = Figure()
            fc = FigureCanvas(fig)
            fc.mpl_connect("button_press_event", self.canvas_clicked)

            for i, image in enumerate(images):
                modality = image['modality']
                img = image['image']

                if modality in LABEL_PREFIX:
                    if stage_num > NO_HINT_LIMIT:
                        continue

                    cmap = 'jet'
                    vmin = LABEL_VMIN
                    vmax = LABEL_VMAX

                else:
                    cmap = 'gray'
                    vmin = img.min()
                    vmax = img.max()

                fc.axes = fig.add_subplot(n_images, 1, i + 1)
                fc.axes.axis('off')
                fig.tight_layout()
                fc.axes.imshow(img, cmap=cmap, vmin=vmin, vmax=vmax)
                fc.axes.set_title(modality.upper())

            FigureCanvas.setSizePolicy(fc,
                                       QSizePolicy.Expanding,
                                       QSizePolicy.Expanding)
            FigureCanvas.updateGeometry(fc)

            self.vLayout_2.addWidget(fc)

        elif self.config['type'] == 'text':
            self.patient_id = None
            self.questionLabel = QLabel(self.groupBox)
            self.questionLabel.setWordWrap(True)
            self.questionLabel.setText('"' + self.config['statement'] + '"')
            self.questionLabel.setFont(font_semibold)
            self.vLayout_2.addWidget(self.questionLabel)

        if self.config['type'] == 'text':
            spacerItem_2 = QSpacerItem(
                20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
            self.vLayout_1.addItem(spacerItem_2)

        self.setWidget(self.widget)
