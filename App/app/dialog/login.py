from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QPushButton

from ..utils import load_config
from .ui_login import Ui_LoginDialog


class LoginDialog(QDialog, Ui_LoginDialog):

    def __init__(self, config):
        super().__init__()

        self.config = config

        self.setupUi(self)
        self.initComboBoxes()
        self.setActions()
        self.setWindowTitle("Login")
        self.show()

    def initComboBoxes(self):
        default_dataset_type = list(self.config['dataset_types'].keys())[0]
        default_model = list(self.config['dataset_types']
                             [default_dataset_type]['models'].keys())[0]

        self.datasetSelection.addItems([default_dataset_type])

        # In the public version, only the MICCAI BraTS 2019 dataset is available.
        self.datasetSelection.setEnabled(False)

        # In the public version, only one model is available.
        self.modelSelection.addItems([default_model])

        self.modelSelection.setEnabled(False)

    def setActions(self):
        self.loginButton.clicked.connect(self.loginButtonClicked)
        self.demoButton.clicked.connect(self.demoButtonClicked)

    def loginButtonClicked(self):
        self.accept()
        self.close()

    def demoButtonClicked(self):
        self.reject()
        self.close()
