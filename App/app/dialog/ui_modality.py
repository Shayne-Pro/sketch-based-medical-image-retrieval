# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'modality_selection.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ModalitySelection(object):
    def setupUi(self, ModalitySelection):
        ModalitySelection.setObjectName("ModalitySelection")
        ModalitySelection.resize(400, 150)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        ModalitySelection.setFont(font)
        self.verticalLayout = QtWidgets.QVBoxLayout(ModalitySelection)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 27, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.modalityLabel = QtWidgets.QLabel(ModalitySelection)
        self.modalityLabel.setObjectName("modalityLabel")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.modalityLabel)
        self.modalityComboBox = QtWidgets.QComboBox(ModalitySelection)
        self.modalityComboBox.setObjectName("modalityComboBox")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.modalityComboBox)
        self.verticalLayout.addLayout(self.formLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(ModalitySelection)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        spacerItem1 = QtWidgets.QSpacerItem(20, 27, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)

        self.retranslateUi(ModalitySelection)
        self.buttonBox.rejected.connect(ModalitySelection.reject)
        self.buttonBox.accepted.connect(ModalitySelection.accept)
        QtCore.QMetaObject.connectSlotsByName(ModalitySelection)

    def retranslateUi(self, ModalitySelection):
        _translate = QtCore.QCoreApplication.translate
        ModalitySelection.setWindowTitle(_translate("ModalitySelection", "Modality selection"))
        self.modalityLabel.setText(_translate("ModalitySelection", "Modality"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ModalitySelection = QtWidgets.QDialog()
    ui = Ui_ModalitySelection()
    ui.setupUi(ModalitySelection)
    ModalitySelection.show()
    sys.exit(app.exec_())
