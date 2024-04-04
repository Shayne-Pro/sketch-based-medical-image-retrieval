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
from PyQt5.QtWidgets import QMessageBox

from .ui_user import Ui_UserDialog


class UserDialog(QDialog, Ui_UserDialog):

    def __init__(self, parent, freeze):
        super().__init__(parent)

        self.parent = parent
        self.setupUi(self)
        self.setActions()

        if freeze:
            self.freezeInformation()

        else:
            self.yearsOfExperienceComboBox.addItems(
                [str(y) for y in range(1, 51)]
            )

        self.setWindowTitle('User')
        self.show()

    def freezeInformation(self):
        existing_user_name = self.parent.app_controller.app_state['user']
        existing_y_experience = self.parent.app_controller.app_state['y_experience']

        self.userNameLineEdit.setText(existing_user_name)
        self.userNameLineEdit.setEnabled(False)
        self.yearsOfExperienceComboBox.addItems([str(existing_y_experience)])
        self.yearsOfExperienceComboBox.setEnabled(False)

    def setActions(self):
        self.buttonBox.accepted.connect(self.button_accepted)
        self.buttonBox.rejected.connect(self.reject)

    def button_accepted(self):
        user_name = self.userNameLineEdit.text()

        if len(user_name) == 0:
            QMessageBox.warning(
                self, 'WARNING', 'User name should have more than one word.',
                QMessageBox.Yes,
            )

        else:
            self.accept()
            self.close()
