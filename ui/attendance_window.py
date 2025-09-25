# attendance_window.py
from database import get_connection
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QComboBox, QDateEdit, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QDate
from models import Absence, Trainee
from utils.security import has_permission, log_activity
from datetime import datetime
import os

class AttendanceWindow(QWidget):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.init_ui()
        self.load_trainees()  # تحميل قائمة المتربصين للاختيار
        self.load_absences()  # تحميل الغيابات
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayoutDirection(Qt.RightToLeft)
        
        # حقول الإدخال لتسجيل غياب
        input_layout = QHBoxLayout()
        
        self.trainee_combo = QComboBox()  # قائمة المتربصين
        input_layout.addWidget(QLabel('المتربص:'))
        input_layout.addWidget(self.trainee_combo)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        input_layout.addWidget(QLabel('التاريخ:'))
        input_layout.addWidget(self.date_edit)
        
        self.session_combo = QComboBox()
        self.session_combo.addItems(['يوم كامل', 'حصة صباحية', 'حصة مسائية'])
        input_layout.addWidget(QLabel('نوع الجلسة:'))
        input_layout.addWidget(self.session_combo)
        
        self.reason_edit = QLineEdit()
        input_layout.addWidget(QLabel('سبب الغياب:'))
        input_layout.addWidget(self.reason_edit)
        
        layout.addLayout(input_layout)
        
        # أزرار
        btn_layout = QHBoxLayout()
        add_btn = QPushButton('تسجيل غياب')
        add_btn.clicked.connect(self.add_absence)
        if has_permission(self.user_role, 'manager'):
            btn_layout.addWidget(add_btn)
        
        justify_btn = QPushButton('إضافة تبرير (وثيقة)')
        justify_btn.clicked.connect(self.add_justification)
        btn_layout.addWidget(justify_btn)
        
        report_btn = QPushButton('استخراج تقرير')
        report_btn.clicked.connect(self.generate_attendance_report)
        btn_layout.addWidget(report_btn)
        
        layout.addLayout(btn_layout)
        
        # جدول الغيابات
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID', 'المتربص ID', 'التاريخ', 'نوع الجلسة', 'السبب', 'مسار التبرير'])
        self.table.itemClicked.connect(self.on_table_click)  # للتعديل
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_trainees(self):
        """تحميل المتربصين في القائمة."""
        data = Trainee.read_all()
        self.trainee_combo.clear()
        for trainee in data:
            self.trainee_combo.addItem(f"{trainee[1]} (ID: {trainee[0]})", trainee[0])
    
    def load_absences(self):
        """تحميل الغيابات في الجدول."""
        conn = get_connection()  # من database.py
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM absences ORDER BY date DESC')
        data = cursor.fetchall()
        self.table.setRowCount(len(data))
        for row, absence in enumerate(data):
            for col, value in enumerate(absence):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
        conn.close()
    
    def add_absence(self):
        """تسجيل غياب جديد."""
        trainee_text = self.trainee_combo.currentText()
        if not trainee_text:
            QMessageBox.warning(self, 'خطأ', 'اختر متربص.')
            return
        trainee_id = self.trainee_combo.itemData(self.trainee_combo.currentIndex())
        date = self.date_edit.date().toString('yyyy-MM-dd')
        session_type = self.session_combo.currentText()
        reason = self.reason_edit.text()
        
        Absence.create(trainee_id, date, session_type, reason)
        log_activity('current_user', f'تسجيل غياب لمتربص ID: {trainee_id}')
        self.load_absences()
        self.clear_inputs()
        QMessageBox.information(self, 'نجح', 'تم تسجيل الغياب.')
    
    def add_justification(self):
        """إضافة وثيقة تبرير للغياب المحدد."""
        row = self.table.currentRow()
        if row >= 0:
            absence_id = int(self.table.item(row, 0).text())
            file_path, _ = QFileDialog.getOpenFileName(self, 'اختر وثيقة تبرير', '', 'PDF (*.pdf);;Images (*.png *.jpg)')
            if file_path:
                # نسخ الملف إلى documents/
                os.makedirs('documents', exist_ok=True)
                dest_path = os.path.join('documents', os.path.basename(file_path))
                import shutil
                shutil.copy2(file_path, dest_path)
                
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE absences SET justification_path=? WHERE id=?', (dest_path, absence_id))
                conn.commit()
                conn.close()
                self.load_absences()
                log_activity('current_user', f'إضافة تبرير للغياب ID: {absence_id}')
        else:
            QMessageBox.warning(self, 'خطأ', 'اختر غياب لإضافة تبرير.')
    
    def generate_attendance_report(self):
        """توليد تقرير حضور/غياب (مثال: غيابات الشهر الحالي)."""
        from models import generate_report
        # استعلام بسيط للغيابات الشهرية
        current_month = datetime.now().strftime('%Y-%m')
        query = 'SELECT t.name, a.date, a.reason FROM absences a JOIN trainees t ON a.trainee_id = t.id WHERE strftime("%Y-%m", a.date) = ?'
        data = generate_report(query, (current_month,), 'pdf')  # أو 'excel'
        QMessageBox.information(self, 'نجح', f'تم تصدير التقرير إلى: {data}')
    
    def on_table_click(self, item):
        """تحميل بيانات الغياب المحدد للتعديل."""
        row = item.row()
        self.trainee_combo.setCurrentText(f"{self.table.item(row, 1).text()}")  # تحديث الحقول
        # ... (يمكن إضافة تعديل كامل)
    
    def clear_inputs(self):
        self.reason_edit.clear()
        self.session_combo.setCurrentIndex(0)
