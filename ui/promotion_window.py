# promotion_window.py
from database import get_connection
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QComboBox, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from models import Promotion, Batch
from utils.security import has_permission, log_activity
from utils.exporter import export_to_pdf  # لإنشاء محضر بسيط
import os
import shutil

class PromotionWindow(QWidget):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.init_ui()
        self.load_batches()
        self.load_promotions()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayoutDirection(Qt.RightToLeft)
        
        # حقول الإدخال
        input_layout = QHBoxLayout()
        
        self.batch_combo = QComboBox()
        input_layout.addWidget(QLabel('الفوج:'))
        input_layout.addWidget(self.batch_combo)
        
        self.from_period_edit = QLineEdit('سداسي أول')
        input_layout.addWidget(QLabel('من السداسي:'))
        input_layout.addWidget(self.from_period_edit)
        
        self.to_period_edit = QLineEdit('سداسي ثاني')
        input_layout.addWidget(QLabel('إلى السداسي:'))
        input_layout.addWidget(self.to_period_edit)
        
        layout.addLayout(input_layout)
        
        # أزرار
        btn_layout = QHBoxLayout()
        promote_btn = QPushButton('ترقية الفوج')
        promote_btn.clicked.connect(self.promote_batch)
        if has_permission(self.user_role, 'admin'):
            btn_layout.addWidget(promote_btn)
        
        minutes_btn = QPushButton('رفع محضر (PDF)')
        minutes_btn.clicked.connect(self.add_minutes)
        btn_layout.addWidget(minutes_btn)
        
        layout.addLayout(btn_layout)
        
        # جدول الترقيات
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['ID', 'الفوج ID', 'من السداسي', 'إلى السداسي', 'مسار المحضر'])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_batches(self):
        """تحميل الأفواج."""
        data = Batch.read_all()
        self.batch_combo.clear()
        for batch in data:
            self.batch_combo.addItem(f"{batch[1]} (ID: {batch[0]})", batch[0])
    
    def load_promotions(self):
        """تحميل الترقيات."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM promotions ORDER BY date DESC')
        data = cursor.fetchall()
        self.table.setRowCount(len(data))
        for row, prom in enumerate(data):
            for col, value in enumerate(prom):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
        conn.close()
    
    def promote_batch(self):
        """ترقية الفوج."""
        batch_id = self.batch_combo.itemData(self.batch_combo.currentIndex())
        if not batch_id:
            QMessageBox.warning(self, 'خطأ', 'اختر فوج.')
            return
        from_period = self.from_period_edit.text()
        to_period = self.to_period_edit.text()
        
        # إنشاء محضر بسيط PDF تلقائيًا
        header = [('الفوج', batch_id), ('من', from_period), ('إلى', to_period), ('التاريخ', datetime.now().strftime('%Y-%m-%d'))]
        minutes_path = export_to_pdf(header, f'محضر ترقية فوج {batch_id}')
        
        Promotion.create(batch_id, from_period, to_period, minutes_path)
        log_activity('current_user', f'ترقية فوج ID: {batch_id}')
        self.load_promotions()
        self.clear_inputs()
        QMessageBox.information(self, 'نجح', 'تم الترقية وإنشاء المحضر.')
    
    def add_minutes(self):
        """رفع محضر PDF موجود."""
        row = self.table.currentRow()
        if row >= 0:
            promotion_id = int(self.table.item(row, 0).text())
            file_path, _ = QFileDialog.getOpenFileName(self, 'اختر محضر PDF', '', 'PDF (*.pdf)')
            if file_path:
                os.makedirs('documents', exist_ok=True)
                dest_path = os.path.join('documents', os.path.basename(file_path))
                shutil.copy2(file_path, dest_path)
                
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE promotions SET minutes_path=? WHERE id=?', (dest_path, promotion_id))
                conn.commit()
                conn.close()
                self.load_promotions()
                log_activity('current_user', f'رفع محضر لترقية ID: {promotion_id}')
        else:
            QMessageBox.warning(self, 'خطأ', 'اختر ترقية.')
    
    def clear_inputs(self):
        self.from_period_edit.clear()
        self.to_period_edit.clear()