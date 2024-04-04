import torch
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import qApp
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QToolBar

from .query_widget import QueryWidget
from .result_widget import ResultWidget
from .question_widget import QuestionWidget
from .result_widget import DemoResultWidget
from .viewer_widget import ViewerWidget
from ..dialog import UserDialog


class MainWindow(QMainWindow):

    def __init__(self, mode, app_controller):
        super().__init__()

        self.mode = mode
        self.app_controller = app_controller

        if self.mode == 'testing':
            self.init_testing_mode()

        elif self.mode == 'interactive':
            self.init_interactive_mode()

        self.viewer_widget = None

        self.setWindowTitle(
            'Model: {} - {}'.format(self.app_controller.app_state['dataset_name'], self.mode))
        self.init_menu_bar()
        self.showMaximized()
        self.show()

    def init_testing_mode(self):
        self.nav_widget = QuestionWidget(self, self.app_controller)
        self.query_widget = QueryWidget(self, self.app_controller)
        self.result_widget = ResultWidget(
            self,
            self.app_controller,
            minimum_width=self.app_controller.gl_config['app']['result']['min_width'],
            minimum_height=self.app_controller.gl_config['app']['result']['min_height'],
        )

        self.app_controller.register_widget(self.nav_widget, 'nav')
        self.app_controller.register_widget(self.query_widget, 'query')
        self.app_controller.register_widget(self.result_widget, 'result')

        self.central_widget = QWidget()
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.query_widget)
        self.central_widget.setLayout(self.hbox)

        self.setCentralWidget(self.central_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.nav_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.result_widget)

    def init_interactive_mode(self):
        self.query_widget = QueryWidget(self, self.app_controller)
        self.result_widget = DemoResultWidget(
            self,
            self.app_controller,
            minimum_width=self.app_controller.gl_config['app']['result']['min_width'],
            minimum_height=self.app_controller.gl_config['app']['result']['min_height'],
        )

        self.app_controller.register_widget(self.query_widget, 'query')
        self.app_controller.register_widget(self.result_widget, 'result')

        self.central_widget = QWidget()
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.query_widget)
        self.central_widget.setLayout(self.hbox)

        self.setCentralWidget(self.central_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.result_widget)

    def run_viewer(self, patient_id, image_path,
                   window_width=None,
                   window_center=None,
                   viewer_title=None,
                   selected_slice=None):
        self.viewer_widget = ViewerWidget(
            main_widget=self,
            app_controller=self.app_controller,
            window_width=window_width,
            window_center=window_center,
        )

        self.addDockWidget(Qt.BottomDockWidgetArea, self.viewer_widget)
        self.viewer_widget.setFloating(True)
        self.viewer_widget.init_viewer(
            patient_id, image_path, viewer_title, selected_slice)

    def init_menu_bar(self, *args, **kwargs):
        if self.mode == 'testing':
            user_action = QAction('&User information', self)
            user_action.setStatusTip('Edit user information')
            user_action.triggered.connect(
                lambda: self.edit_user_information(freeze=True)
            )

        show_help_action = QAction('&Help', self)
        show_help_action.setStatusTip('Help')
        show_help_action.triggered.connect(self.show_help)

        show_credit_action = QAction('&Credit', self)
        show_credit_action.setStatusTip('Credit')
        show_credit_action.triggered.connect(self.show_credit)

        if self.mode == 'testing':
            user_menu = self.menuBar().addMenu('&User')
            user_menu.addAction(user_action)

        help_menu = self.menuBar().addMenu('&Help')
        help_menu.addAction(show_help_action)
        help_menu.addAction(show_credit_action)

    def edit_user_information(self, freeze):
        user_dialog = UserDialog(self, freeze=freeze)

        if user_dialog.exec_() == QDialog.Accepted:
            user_name = user_dialog.userNameLineEdit.text()
            y_experience = int(
                user_dialog.yearsOfExperienceComboBox.currentText())

        else:
            user_name = 'Test'
            y_experience = 0

        if not freeze:
            self.app_controller.app_state['user'] = user_name
            self.app_controller.app_state['y_experience'] = y_experience

    def show_help(self):
        print('show_help')

    def show_credit(self):
        print('show_credit')
