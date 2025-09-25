# trainees_window.py
from database import get_connection
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QFileDialog, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from models import Trainee, Batch
from utils.security import has_permission, log_activity
import os

class TraineesWindow(QWidget):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.init_ui()
        self.load_trainees()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayoutDirection(Qt.RightToLeft)
        
        # حقول الإدخال
        input_layout = QHBoxLayout()
        
        self.name_edit = QLineEdit()
        input_layout.addWidget(QLabel('الاسم:'))
        input_layout.addWidget(self.name_edit)
        
        self.age_edit = QLineEdit()
        input_layout.addWidget(QLabel('العمر:'))
        input_layout.addWidget(self.age_edit)
        
        self.specialty_edit = QLineEdit()
        input_layout.addWidget(QLabel('التخصص:'))
        input_layout.addWidget(self.specialty_edit)
        
        self.batch_combo = QComboBox()
        self.load_batches()  # تحميل الأفواج
        input_layout.addWidget(QLabel('الفوج:'))
        input_layout.addWidget(self.batch_combo)
        
        layout.addLayout(input_layout)
        
        # أزرار (مع التحقق من الصلاحيات)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton('إضافة')
        add_btn.clicked.connect(self.add_trainee)
        if has_permission(self.user_role, 'manager'):
            btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton('تعديل')
        edit_btn.clicked.connect(self.edit_trainee)
        if has_permission(self.user_role, 'manager'):
            btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton('حذف')
        delete_btn.clicked.connect(self.delete_trainee)
        if has_permission(self.user_role, 'admin'):
            btn_layout.addWidget(delete_btn)
        
        search_btn = QPushButton('بحث')
        search_btn.clicked.connect(self.search_trainee)
        btn_layout.addWidget(search_btn)
        
        # استيراد Excel/CSV
        import_btn = QPushButton('استيراد من Excel/CSV')
        import_btn.clicked.connect(self.import_from_file)
        btn_layout.addWidget(import_btn)
        
        layout.addLayout(btn_layout)
        
        # جدول العرض
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID', 'الاسم', 'العمر', 'التخصص', 'الفوج', 'تاريخ الالتحاق'])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_trainees(self):
        """تحميل قائمة المتربصين في الجدول."""
        data = Trainee.read_all()
        self.table.setRowCount(len(data))
        for row, trainee in enumerate(data):
            for col, value in enumerate(trainee):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
    
    def load_batches(self):
        """تحميل الأفواج في القائمة المنسدلة."""
        conn = get_connection()  # من database.py
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM batches')
        batches = cursor.fetchall()
        self.batch_combo.addItems([f"{b[1]} (ID: {b[0]})" for b in batches])
        conn.close()
    
    def add_trainee(self):
        """إضافة متربص جديد (مع صورة اختيارية)."""
        name = self.name_edit.text()
        age = int(self.age_edit.text() or 0)
        specialty = self.specialty_edit.text()
        batch_id = int(self.batch_combo.currentText().split('ID: ')[1].split(')')[0]) if self.batch_combo.currentText() else 1
        
        # اختيار صورة
        photo_path = QFileDialog.getOpenFileName(self, 'اختر صورة', '', 'Images (*.png *.jpg)')[0]
        if not photo_path:
            photo_path = ''
        
        trainee_id = Trainee.create(name, age, specialty, photo_path, batch_id)
        log_activity('current_user', f'إضافة متربص ID: {trainee_id}')
        self.load_trainees()
        self.clear_inputs()
        QMessageBox.information(self, 'نجح', 'تم إضافة المتربص بنجاح.')
    
    def edit_trainee(self):
        """تعديل المحدد في الجدول."""
        row = self.table.currentRow()
        if row >= 0:
            trainee_id = int(self.table.item(row, 0).text())
            # تحديث الحقول من الجدول أو إدخال جديد
            name = self.name_edit.text() or self.table.item(row, 1).text()
            age = int(self.age_edit.text() or self.table.item(row, 2).text())
            specialty = self.specialty_edit.text() or self.table.item(row, 3).text()
            Trainee.update(trainee_id, name=name, age=age, specialty=specialty)
            self.load_trainees()
            QMessageBox.information(self, 'نجح', 'تم التعديل.')
        else:
            QMessageBox.warning(self, 'خطأ', 'اختر متربص للتعديل.')
    
    def delete_trainee(self):
        """حذف المحدد."""
        row = self.table.currentRow()
        if row >= 0 and QMessageBox.question(self, 'تأكيد', 'هل تريد الحذف؟') == QMessageBox.Yes:
            trainee_id = int(self.table.item(row, 0).text())
            Trainee.delete(trainee_id)
            self.load_trainees()
    
    def search_trainee(self):
        """بحث."""
        name = self.name_edit.text()
        data = Trainee.search(name)
        self.table.setRowCount(len(data))
        for row, trainee in enumerate(data):
            for col, value in enumerate(trainee):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
    
    def import_from_file(self):
        """استيراد من Excel/CSV (مثال بسيط باستخدام pandas)."""
        file_path, _ = QFileDialog.getOpenFileName(self, 'اختر ملف', '', 'Excel (*.xlsx);;CSV (*.csv)')
        if file_path:
            import pandas as pd
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            for _, row in df.iterrows():
                Trainee.create(row['name'], row['age'], row['specialty'], batch_id=1)
            self.load_trainees()
            QMessageBox.information(self, 'نجح', 'تم الاستيراد.')
    
    def clear_inputs(self):
        self.name_edit.clear()
        self.age_edit.clear()
        self.specialty_edit.clear()
