# disciplinary_window.py
from database import get_connection
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QComboBox, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from models import DisciplinaryAction, Trainee
from utils.security import has_permission, log_activity
from utils.exporter import export_to_pdf
from datetime import datetime
import os
import shutil

class DisciplinaryWindow(QWidget):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.init_ui()
        self.load_trainees()
        self.load_actions()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayoutDirection(Qt.RightToLeft)
        
        # حقول الإدخال
        input_layout = QHBoxLayout()
        
        self.trainee_combo = QComboBox()
        input_layout.addWidget(QLabel('المتربص:'))
        input_layout.addWidget(self.trainee_combo)
        
        self.action_combo = QComboBox()
        self.action_combo.addItems(['إنذار', 'توبيخ', 'محضر مجلس'])
        input_layout.addWidget(QLabel('نوع الإجراء:'))
        input_layout.addWidget(self.action_combo)
        
        self.description_edit = QLineEdit()
        input_layout.addWidget(QLabel('الوصف:'))
        input_layout.addWidget(self.description_edit)
        
        layout.addLayout(input_layout)
        
        # أزرار
        btn_layout = QHBoxLayout()
        add_btn = QPushButton('تسجيل إجراء')
        add_btn.clicked.connect(self.add_action)
        if has_permission(self.user_role, 'manager'):
            btn_layout.addWidget(add_btn)
        
        pdf_btn = QPushButton('إنشاء/رفع محضر PDF')
        pdf_btn.clicked.connect(self.add_pdf)
        btn_layout.addWidget(pdf_btn)
        
        layout.addLayout(btn_layout)
        
        # جدول الإجراءات
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['ID', 'المتربص ID', 'نوع الإجراء', 'الوصف', 'مسار PDF'])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_trainees(self):
        """تحميل المتربصين."""
        data = Trainee.read_all()
        self.trainee_combo.clear()
        for trainee in data:
            self.trainee_combo.addItem(f"{trainee[1]} (ID: {trainee[0]})", trainee[0])
    
    def load_actions(self):
        """تحميل الإجراءات."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM disciplinary_actions ORDER BY date DESC')
        data = cursor.fetchall()
        self.table.setRowCount(len(data))
        for row, action in enumerate(data):
            for col, value in enumerate(action):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
        conn.close()
    
    def add_action(self):
        """تسجيل إجراء تأديبي."""
        trainee_id = self.trainee_combo.itemData(self.trainee_combo.currentIndex())
        if not trainee_id:
            QMessageBox.warning(self, 'خطأ', 'اختر متربص.')
            return
        action_type = self.action_combo.currentText()
        description = self.description_edit.text()
        
        # إنشاء PDF بسيط للمحضر إذا كان 'محضر مجلس'
        pdf_path = ''
        if action_type == 'محضر مجلس':
            header = [('المتربص', trainee_id), ('الإجراء', action_type), ('الوصف', description), ('التاريخ', datetime.now().strftime('%Y-%m-%d'))]
            pdf_path = export_to_pdf(header, f'محضر {action_type} لمتربص {trainee_id}')
        
        DisciplinaryAction.create(trainee_id, action_type, description, pdf_path)
        log_activity('current_user', f'تسجيل إجراء {action_type} لمتربص ID: {trainee_id}')
        self.load_actions()
        self.clear_inputs()
        QMessageBox.information(self, 'نجح', 'تم تسجيل الإجراء.')
    
    def add_pdf(self):
        """رفع PDF لإجراء موجود."""
        row = self.table.currentRow()
        if row >= 0:
            action_id = int(self.table.item(row, 0).text())
            file_path, _ = QFileDialog.getOpenFileName(self, 'اختر محضر PDF', '', 'PDF (*.pdf)')
            if file_path:
                os.makedirs('documents', exist_ok=True)
                dest_path = os.path.join('documents', os.path.basename(file_path))
                shutil.copy2(file_path, dest_path)
                
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE disciplinary_actions SET pdf_path=? WHERE id=?', (dest_path, action_id))
                conn.commit()
                conn.close()
                self.load_actions()
                log_activity('current_user', f'رفع PDF لإجراء ID: {action_id}')
        else:
            QMessageBox.warning(self, 'خطأ', 'اختر إجراء.')
    
    def clear_inputs(self):
        self.description_edit.clear()
        self.action_combo.setCurrentIndex(0)