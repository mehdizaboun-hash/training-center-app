# login_window.py
from database import get_connection
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt
from utils.security import authenticate

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('تسجيل الدخول - نظام إدارة التكوين المهني')
        self.setFixedSize(300, 200)
        self.setLayoutDirection(Qt.RightToLeft)  # RTL للعربية
        
        layout = QVBoxLayout()
        
        # اسم المستخدم
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel('اسم المستخدم:'))
        self.username_edit = QLineEdit()
        username_layout.addWidget(self.username_edit)
        layout.addLayout(username_layout)
        
        # كلمة المرور
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel('كلمة المرور:'))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self.password_edit)
        layout.addLayout(password_layout)
        
        # زر تسجيل الدخول
        login_btn = QPushButton('دخول')
        login_btn.clicked.connect(self.login)
        layout.addWidget(login_btn)
        
        self.setLayout(layout)
        self.user_id = None
        self.user_role = None
    
    def login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        self.user_id, self.user_role = authenticate(username, password)
        if self.user_id:
            self.accept()  # إغلاق النافذة وتمرير البيانات
        else:
            QMessageBox.warning(self, 'خطأ', 'اسم المستخدم أو كلمة المرور غير صحيحة.')
