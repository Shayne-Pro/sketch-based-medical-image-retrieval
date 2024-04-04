# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\login_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_LoginDialog(object):
    def setupUi(self, LoginDialog):
        LoginDialog.setObjectName("LoginDialog")
        LoginDialog.resize(
            LoginDialog.config['app']['login']['size'][0],
            LoginDialog.config['app']['login']['size'][1])
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        LoginDialog.setFont(font)
        LoginDialog.setWindowTitle("Login")
        self.verticalLayout = QtWidgets.QVBoxLayout(LoginDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtWidgets.QSpacerItem(
            20, 4, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem1 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.loginIcon = QtWidgets.QLabel(LoginDialog)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.loginIcon.sizePolicy().hasHeightForWidth())
        self.loginIcon.setSizePolicy(sizePolicy)
        self.loginIcon.setText("")
        self.loginIcon.setPixmap(QtGui.QPixmap(
            LoginDialog.config['static']['icon_path']))
        self.loginIcon.setScaledContents(True)
        self.loginIcon.setAlignment(QtCore.Qt.AlignCenter)
        self.loginIcon.setObjectName("loginIcon")
        self.horizontalLayout_2.addWidget(self.loginIcon)
        spacerItem2 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.loginLabel = QtWidgets.QLabel(LoginDialog)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        self.loginLabel.setFont(font)
        self.loginLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.loginLabel.setObjectName("loginLabel")
        self.verticalLayout.addWidget(self.loginLabel)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem3 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem3)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.datasetLabel = QtWidgets.QLabel(LoginDialog)
        self.datasetLabel.setObjectName("datasetLabel")
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, self.datasetLabel)
        self.datasetSelection = QtWidgets.QComboBox(LoginDialog)
        self.datasetSelection.setObjectName("datasetSelection")
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.datasetSelection)
        self.modelLabel = QtWidgets.QLabel(LoginDialog)
        self.modelLabel.setObjectName("modelLabel")
        self.formLayout.setWidget(
            1, QtWidgets.QFormLayout.LabelRole, self.modelLabel)
        self.modelSelection = QtWidgets.QComboBox(LoginDialog)
        self.modelSelection.setObjectName("modelSelection")
        self.formLayout.setWidget(
            1, QtWidgets.QFormLayout.FieldRole, self.modelSelection)
        self.horizontalLayout_3.addLayout(self.formLayout)
        spacerItem4 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem4)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem5 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem5)
        self.loginButton = QtWidgets.QPushButton(LoginDialog)
        self.loginButton.setObjectName("loginButton")
        self.horizontalLayout.addWidget(self.loginButton)
        self.demoButton = QtWidgets.QPushButton(LoginDialog)
        self.demoButton.setObjectName("demoButton")
        self.horizontalLayout.addWidget(self.demoButton)
        spacerItem6 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem6)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.label = QtWidgets.QLabel(LoginDialog)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        spacerItem7 = QtWidgets.QSpacerItem(
            20, 5, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem7)

        self.retranslateUi(LoginDialog)
        QtCore.QMetaObject.connectSlotsByName(LoginDialog)

    def retranslateUi(self, LoginDialog):
        _translate = QtCore.QCoreApplication.translate
        self.loginLabel.setText(_translate(
            "LoginDialog", "Demo application for sketch-based medical image retrieval."))
        self.datasetLabel.setText(_translate("LoginDialog", "Dataset"))
        self.modelLabel.setText(_translate("LoginDialog", "Model"))
        self.loginButton.setText(_translate("LoginDialog", "Testing"))
        self.demoButton.setText(_translate("LoginDialog", "Interactive"))
        self.label.setText(_translate(
            "LoginDialog", "© 2023 Kazuma Kobayashi"))
