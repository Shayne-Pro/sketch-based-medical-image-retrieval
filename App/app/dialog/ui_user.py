# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\user.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_UserDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(234, 170)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        Dialog.setFont(font)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 27, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.userNameLineEdit = QtWidgets.QLineEdit(Dialog)
        self.userNameLineEdit.setObjectName("userNameLineEdit")
        self.userNameLineEdit.setMinimumWidth(200)
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.userNameLineEdit)
        self.yearsOfExperienceLabel = QtWidgets.QLabel(Dialog)
        self.yearsOfExperienceLabel.setObjectName("yearsOfExperienceLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.yearsOfExperienceLabel)
        self.yearsOfExperienceComboBox = QtWidgets.QComboBox(Dialog)
        self.yearsOfExperienceComboBox.setObjectName("yearsOfExperienceComboBox")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.yearsOfExperienceComboBox)
        self.userNameLabel = QtWidgets.QLabel(Dialog)
        self.userNameLabel.setObjectName("userNameLabel")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.userNameLabel)
        self.verticalLayout.addLayout(self.formLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        spacerItem1 = QtWidgets.QSpacerItem(20, 27, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.yearsOfExperienceLabel.setText(_translate("Dialog", "Years of experience"))
        self.userNameLabel.setText(_translate("Dialog", "User name"))
