# documents_window.py
from database import get_connection
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QComboBox, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from models import Document, Trainee
from utils.scanner import scan_document
from utils.security import has_permission, log_activity
import os
import shutil

class DocumentsWindow(QWidget):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.init_ui()
        self.load_trainees()
        self.load_documents()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayoutDirection(Qt.RightToLeft)
        
        # حقول الإدخال
        input_layout = QHBoxLayout()
        
        self.trainee_combo = QComboBox()
        input_layout.addWidget(QLabel('المتربص:'))
        input_layout.addWidget(self.trainee_combo)
        
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.addItems(['هوية', 'شهادة', 'شهادة طبية', 'أخرى'])
        input_layout.addWidget(QLabel('نوع الوثيقة:'))
        input_layout.addWidget(self.doc_type_combo)
        
        layout.addLayout(input_layout)
        
        # أزرار
        btn_layout = QHBoxLayout()
        import_btn = QPushButton('استيراد ملف')
        import_btn.clicked.connect(self.import_document)
        if has_permission(self.user_role, 'manager'):
            btn_layout.addWidget(import_btn)
        
        scan_btn = QPushButton('مسح ضوئي')
        scan_btn.clicked.connect(self.scan_and_add)
        btn_layout.addWidget(scan_btn)
        
        view_btn = QPushButton('عرض/طباعة')
        view_btn.clicked.connect(self.view_document)
        btn_layout.addWidget(view_btn)
        
        layout.addLayout(btn_layout)
        
        # جدول الوثائق
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['ID', 'المتربص ID', 'نوع الوثيقة', 'مسار الملف', 'تاريخ الرفع'])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_trainees(self):
        """تحميل المتربصين."""
        data = Trainee.read_all()
        self.trainee_combo.clear()
        for trainee in data:
            self.trainee_combo.addItem(f"{trainee[1]} (ID: {trainee[0]})", trainee[0])
    
    def load_documents(self):
        """تحميل الوثائق."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents ORDER BY upload_date DESC')
        data = cursor.fetchall()
        self.table.setRowCount(len(data))
        for row, doc in enumerate(data):
            for col, value in enumerate(doc):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
        conn.close()
    
    def import_document(self):
        """استيراد ملف وثيقة."""
        trainee_id = self.trainee_combo.itemData(self.trainee_combo.currentIndex())
        if not trainee_id:
            QMessageBox.warning(self, 'خطأ', 'اختر متربص.')
            return
        file_path, _ = QFileDialog.getOpenFileName(self, 'اختر وثيقة', '', 'PDF (*.pdf);;Images (*.png *.jpg *.jpeg)')
        if file_path:
            # نسخ إلى documents/
            os.makedirs('documents', exist_ok=True)
            dest_path = os.path.join('documents', os.path.basename(file_path))
            shutil.copy2(file_path, dest_path)
            doc_type = self.doc_type_combo.currentText()
            Document.create(trainee_id, doc_type, dest_path)
            log_activity('current_user', f'إضافة وثيقة لمتربص ID: {trainee_id}')
            self.load_documents()
            QMessageBox.information(self, 'نجح', 'تم استيراد الوثيقة.')
    
    def scan_and_add(self):
        """مسح ضوئي وإضافة."""
        trainee_id = self.trainee_combo.itemData(self.trainee_combo.currentIndex())
        if not trainee_id:
            QMessageBox.warning(self, 'خطأ', 'اختر متربص.')
            return
        scanned_path = scan_document()
        if scanned_path:
            doc_type = self.doc_type_combo.currentText()
            Document.create(trainee_id, doc_type, scanned_path)
            log_activity('current_user', f'مسح وإضافة وثيقة لمتربص ID: {trainee_id}')
            self.load_documents()
            QMessageBox.information(self, 'نجح', 'تم المسح والإضافة.')
    
    def view_document(self):
        """عرض أو طباعة الوثيقة المحددة."""
        row = self.table.currentRow()
        if row >= 0:
            file_path = self.table.item(row, 3).text()
            if os.path.exists(file_path):
                os.startfile(file_path)  # فتح في البرنامج الافتراضي (Windows)
                # للطباعة: يمكن إضافة QPrintDialog هنا
            else:
                QMessageBox.warning(self, 'خطأ', 'الملف غير موجود.')
        else:
            QMessageBox.warning(self, 'خطأ', 'اختر وثيقة.')
