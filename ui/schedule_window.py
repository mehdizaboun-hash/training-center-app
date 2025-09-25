# schedule_window.py
from database import get_connection
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QComboBox, QMessageBox)
from PyQt5.QtCore import Qt
from models import Schedule, Batch, Trainee
from utils.security import has_permission, log_activity

class ScheduleWindow(QWidget):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.init_ui()
        self.load_batches()
        self.load_schedules()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayoutDirection(Qt.RightToLeft)
        
        # حقول الإدخال
        input_layout = QHBoxLayout()
        
        self.day_combo = QComboBox()
        self.day_combo.addItems(['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'])
        input_layout.addWidget(QLabel('اليوم:'))
        input_layout.addWidget(self.day_combo)
        
        self.time_edit = QLineEdit('08:00-10:00')  # مثال
        input_layout.addWidget(QLabel('الوقت:'))
        input_layout.addWidget(self.time_edit)
        
        self.subject_edit = QLineEdit()
        input_layout.addWidget(QLabel('المادة:'))
        input_layout.addWidget(self.subject_edit)
        
        self.batch_combo = QComboBox()
        input_layout.addWidget(QLabel('الفوج:'))
        input_layout.addWidget(self.batch_combo)
        
        layout.addLayout(input_layout)
        
        # أزرار
        btn_layout = QHBoxLayout()
        add_btn = QPushButton('إضافة حصة')
        add_btn.clicked.connect(self.add_schedule)
        if has_permission(self.user_role, 'manager'):
            btn_layout.addWidget(add_btn)
        
        print_btn = QPushButton('طباعة الجدول')
        print_btn.clicked.connect(self.print_schedule)
        btn_layout.addWidget(print_btn)
        
        layout.addLayout(btn_layout)
        
        # جدول الجداول
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['ID', 'اليوم', 'الوقت', 'المادة', 'الفوج ID'])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_batches(self):
        """تحميل الأفواج."""
        data = Batch.read_all()  # افترض دالة read_all في Batch مشابهة لـTrainee
        self.batch_combo.clear()
        for batch in data:
            self.batch_combo.addItem(f"{batch[1]} (ID: {batch[0]})", batch[0])
    
    def load_schedules(self):
        """تحميل الجداول."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM schedules ORDER BY day')
        data = cursor.fetchall()
        self.table.setRowCount(len(data))
        for row, sched in enumerate(data):
            for col, value in enumerate(sched):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
        conn.close()
    
    def add_schedule(self):
        """إضافة حصة جديدة."""
        day = self.day_combo.currentText()
        time_slot = self.time_edit.text()
        subject = self.subject_edit.text()
        batch_id = self.batch_combo.itemData(self.batch_combo.currentIndex())
        
        Schedule.create(day, time_slot, subject, batch_id)
        log_activity('current_user', f'إضافة حصة: {subject}')
        self.load_schedules()
        self.clear_inputs()
        QMessageBox.information(self, 'نجح', 'تم إضافة الحصة.')
    
    def print_schedule(self):
        """طباعة الجدول الأسبوعي (مثال بسيط)."""
        from utils.exporter import export_to_pdf
        conn = get_connection()
        cursor = conn.cursor()
                cursor.execute('SELECT * FROM schedules ORDER BY day')
        data = cursor.fetchall()
        # إضافة عناوين للتقرير
        header = [('ID', 'اليوم', 'الوقت', 'المادة', 'الفوج ID')]
        report_data = header + [list(row) for row in data]
        filename = export_to_pdf(report_data, 'جدول الحصص الأسبوعي')
        conn.close()
        QMessageBox.information(self, 'نجح', f'تم تصدير الجدول إلى PDF: {filename}')
        # للطباعة المباشرة: يمكن إضافة QPrinter هنا (مثل في reports_window)
    
    def clear_inputs(self):
        """مسح الحقول."""
        self.time_edit.clear()
        self.subject_edit.clear()
        self.day_combo.setCurrentIndex(0)
        self.batch_combo.setCurrentIndex(0)

# دالة read_all لـBatch (أضفها في models.py إذا لم تكن موجودة)
class Batch:
    # ... (الكود السابق)
    @staticmethod
    def read_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM batches')
        return cursor.fetchall()