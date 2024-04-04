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
from .ui_modality import Ui_ModalitySelection


class ModalityDialog(QDialog, Ui_ModalitySelection):

    def __init__(self, ds_config):
        super().__init__()

        self.brats_config = ds_config
        self.brats_modalities = self.brats_config['reference']['modalities'][:-1]

        self.setupUi(self)
        self.initComboBoxes()
        self.show()

    def initComboBoxes(self):
        _modalities = [m.upper() for m in self.brats_modalities]
        self.modalityComboBox.addItems(_modalities)
