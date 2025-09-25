from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QComboBox, QDateEdit, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from models import generate_report, Trainee, Absence
from utils.security import has_permission, log_activity
from utils.exporter import export_to_pdf, export_to_excel, print_report  # print_report هنا للطباعة
from datetime import datetime
from database import get_connection
class ReportsWindow(QWidget):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.init_ui()
        self.load_sample_report()  # تحميل تقرير عينة
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayoutDirection(Qt.RightToLeft)
        
        # خيارات التقارير
        options_layout = QHBoxLayout()
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(['تقرير فردي', 'تقرير حسب الفوج', 'تقرير حسب التخصص', 'إحصائيات غياب شهرية'])
        options_layout.addWidget(QLabel('نوع التقرير:'))
        options_layout.addWidget(self.report_type_combo)
        
        self.trainee_combo = QComboBox()  # للفردي
        options_layout.addWidget(QLabel('المتربص/الفوج:'))
        options_layout.addWidget(self.trainee_combo)
        
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        options_layout.addWidget(QLabel('من تاريخ:'))
        options_layout.addWidget(self.date_from)
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        options_layout.addWidget(QLabel('إلى تاريخ:'))
        options_layout.addWidget(self.date_to)
        
        layout.addLayout(options_layout)
        
        # أزرار
        btn_layout = QHBoxLayout()
        generate_btn = QPushButton('توليد تقرير')
        generate_btn.clicked.connect(self.generate_custom_report)
        if has_permission(self.user_role, 'manager'):
            btn_layout.addWidget(generate_btn)
        
        export_pdf_btn = QPushButton('تصدير PDF')
        export_pdf_btn.clicked.connect(self.export_pdf)
        btn_layout.addWidget(export_pdf_btn)
        
        export_excel_btn = QPushButton('تصدير Excel')
        export_excel_btn.clicked.connect(self.export_excel)
        btn_layout.addWidget(export_excel_btn)
        
        print_btn = QPushButton('طباعة')
        print_btn.clicked.connect(self.print_current_report)
        btn_layout.addWidget(print_btn)
        
        layout.addLayout(btn_layout)
        
        # جدول عرض التقرير
        self.table = QTableWidget()
        self.table.setColumnCount(4)  # مثال
        self.table.setHorizontalHeaderLabels(['الاسم', 'التاريخ', 'الحالة', 'التفاصيل'])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.current_report_data = []  # لحفظ البيانات الحالية
    
       def load_sample_report(self):
        """تحميل تقرير عينة (غيابات حديثة)."""
        query = '''
            SELECT t.name, a.date, a.reason FROM absences a 
            JOIN trainees t ON a.trainee_id = t.id 
            ORDER BY a.date DESC LIMIT 10
            -- للتوسع: JOIN centers c ON t.center_id = c.id WHERE c.id = ? (لربط مراكز متعددة)
        '''
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        # إضافة عناوين
        header = [('الاسم', 'التاريخ', 'السبب')]
        self.current_report_data = header + [list(row) for row in data]
        self.display_report(self.current_report_data)
        conn.close()
    
    def generate_custom_report(self):
        """توليد تقرير مخصص حسب النوع."""
        report_type = self.report_type_combo.currentText()
        trainee_id = self.trainee_combo.itemData(self.trainee_combo.currentIndex()) if self.trainee_combo.count() > 0 else None
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        
        query = ''
        params = (date_from, date_to)
        
        if 'فردي' in report_type and trainee_id:
            query = '''
                SELECT t.name, a.date, a.reason, a.justification_path FROM absences a 
                JOIN trainees t ON a.trainee_id = t.id 
                WHERE a.trainee_id = ? AND a.date BETWEEN ? AND ?
                -- للتوسع: AND t.center_id = ?
            '''
            params = (trainee_id, date_from, date_to)  # أضف center_id إذا لزم
        elif 'حسب الفوج' in report_type:
            # افترض batch_id من combo (أضف تحميل batches في init_ui إذا لزم)
            batch_id = 1  # مثال؛ اجعلها ديناميكية
            query = '''
                SELECT t.name, a.date, a.reason FROM absences a 
                JOIN trainees t ON a.trainee_id = t.id 
                WHERE t.batch_id = ? AND a.date BETWEEN ? AND ?
                -- للتوسع: JOIN centers c ON t.center_id = c.id WHERE c.id = ?
            '''
            params = (batch_id, date_from, date_to)
        elif 'حسب التخصص' in report_type:
            specialty = 'تخصص عام'  # من إدخال نصي؛ أضف QLineEdit
            query = '''
                SELECT t.name, a.date, a.reason FROM absences a 
                JOIN trainees t ON a.trainee_id = t.id 
                WHERE t.specialty = ? AND a.date BETWEEN ? AND ?
            '''
            params = (specialty, date_from, date_to)
        elif 'إحصائيات غياب' in report_type:
            query = '''
                SELECT t.specialty, COUNT(a.id) as num_absences FROM absences a 
                JOIN trainees t ON a.trainee_id = t.id 
                WHERE a.date BETWEEN ? AND ? GROUP BY t.specialty
                -- للتوسع: GROUP BY c.name للمراكز
            '''
        
        if query:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            data = cursor.fetchall()
            header = self.get_header_for_type(report_type)  # دالة مساعدة
            self.current_report_data = header + [list(row) for row in data]
            self.display_report(self.current_report_data)
            conn.close()
            log_activity('current_user', f'توليد تقرير: {report_type}')
            QMessageBox.information(self, 'نجح', 'تم توليد التقرير.')
        else:
            QMessageBox.warning(self, 'خطأ', 'حدد خيارات صحيحة.')
    
    def get_header_for_type(self, report_type):
        """الحصول على عناوين حسب النوع."""
        if 'فردي' in report_type:
            return [('الاسم', 'التاريخ', 'السبب', 'التبرير')]
        elif 'إحصائيات' in report_type:
            return [('التخصص', 'عدد الغيابات')]
        return [('اسم العمود 1', 'اسم العمود 2')]  # افتراضي
    
    def display_report(self, data):
        """عرض التقرير في الجدول."""
        self.table.setRowCount(len(data) - 1)  # بدون العنوان
        self.table.setColumnCount(len(data[0]) if data else 0)
        self.table.setHorizontalHeaderLabels(data[0])
        for row, rec in enumerate(data[1:]):
            for col, value in enumerate(rec):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
    
    def export_pdf(self):
        """تصدير التقرير الحالي إلى PDF."""
        if self.current_report_data:
            filename = export_to_pdf(self.current_report_data, 'تقرير مخصص')
            QMessageBox.information(self, 'نجح', f'تم التصدير إلى: {filename}')
        else:
            QMessageBox.warning(self, 'خطأ', 'لا يوجد تقرير للتصدير.')
    
    def export_excel(self):
        """تصدير التقرير الحالي إلى Excel."""
        if self.current_report_data:
            filename = export_to_excel(self.current_report_data, 'تقرير مخصص')
            QMessageBox.information(self, 'نجح', f'تم التصدير إلى: {filename}')
        else:
            QMessageBox.warning(self, 'خطأ', 'لا يوجد تقرير للتصدير.')
    
    def print_current_report(self):
        """طباعة التقرير الحالي."""
        if not self.current_report_data:
            QMessageBox.warning(self, 'خطأ', 'لا يوجد تقرير للطباعة.')
            return
        
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            from PyQt5.QtGui import QPainter, QTextDocument
            document = QTextDocument()
            # بناء نص التقرير (بسيط؛ يمكن تحسين بـHTML)
            text = '<h1>تقرير مخصص</h1><table border="1">'
            for row in self.current_report_data:
                text += '<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>'
            text += '</table>'
            document.setHtml(text)
            painter = QPainter(printer)
            document.print_(painter)
            painter.end()
            log_activity('current_user', 'طباعة تقرير')
            QMessageBox.information(self, 'نجح', 'تم إرسال التقرير للطباعة.')
# ui/reports_window.py - إضافة الدعم الكامل للطباعة
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QComboBox, QDateEdit, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument, QTextCursor, QTextTableFormat, QTextCharFormat, QFont
from database import get_connection
from models import generate_report
from utils.security import has_permission, log_activity
from utils.exporter import export_to_pdf, export_to_excel
from datetime import datetime

class ReportsWindow(QWidget):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.current_report_data = []
        self.init_ui()
        self.load_sample_report()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayoutDirection(Qt.RightToLeft)
        
        # خيارات التقارير
        options_layout = QHBoxLayout()
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            'تقرير فردي', 
            'تقرير حسب الفوج', 
            'تقرير حسب التخصص', 
            'إحصائيات غياب شهرية',
            'جميع المتربصين',
            'جميع الغيابات'
        ])
        options_layout.addWidget(QLabel('نوع التقرير:'))
        options_layout.addWidget(self.report_type_combo)
        
        self.trainee_combo = QComboBox()
        self.load_trainees()  # تحميل المتربصين
        options_layout.addWidget(QLabel('المتربص:'))
        options_layout.addWidget(self.trainee_combo)
        
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        options_layout.addWidget(QLabel('من تاريخ:'))
        options_layout.addWidget(self.date_from)
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        options_layout.addWidget(QLabel('إلى تاريخ:'))
        options_layout.addWidget(self.date_to)
        
        layout.addLayout(options_layout)
        
        # أزرار
        btn_layout = QHBoxLayout()
        generate_btn = QPushButton('توليد تقرير')
        generate_btn.clicked.connect(self.generate_custom_report)
        btn_layout.addWidget(generate_btn)
        
        export_pdf_btn = QPushButton('تصدير PDF')
        export_pdf_btn.clicked.connect(self.export_pdf)
        btn_layout.addWidget(export_pdf_btn)
        
        export_excel_btn = QPushButton('تصدير Excel')
        export_excel_btn.clicked.connect(self.export_excel)
        btn_layout.addWidget(export_excel_btn)
        
        print_btn = QPushButton('طباعة')
        print_btn.clicked.connect(self.print_current_report)
        btn_layout.addWidget(print_btn)
        
        layout.addLayout(btn_layout)
        
        # جدول عرض التقرير
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['البيان 1', 'البيان 2', 'البيان 3', 'البيان 4'])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_trainees(self):
        """تحميل قائمة المتربصين."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM trainees')
        trainees = cursor.fetchall()
        self.trainee_combo.clear()
        self.trainee_combo.addItem('اختر متربص', -1)
        for trainee_id, name in trainees:
            self.trainee_combo.addItem(f"{name} (ID: {trainee_id})", trainee_id)
        conn.close()
    
    def load_sample_report(self):
        """تحميل تقرير عينة."""
        query = '''
            SELECT t.name, a.date, a.reason, a.session_type 
            FROM absences a 
            JOIN trainees t ON a.trainee_id = t.id 
            ORDER BY a.date DESC LIMIT 10
        '''
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        columns = ['اسم المتربص', 'التاريخ', 'السبب', 'نوع الجلسة']
        self.current_report_data = [columns] + [list(row) for row in data]
        self.display_report(self.current_report_data)
        conn.close()
    
    def generate_custom_report(self):
        """توليد تقرير مخصص."""
        report_type = self.report_type_combo.currentText()
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        
        query = ""
        params = ()
        
        if report_type == 'تقرير فردي':
            trainee_id = self.trainee_combo.itemData(self.trainee_combo.currentIndex())
            if trainee_id == -1:
                QMessageBox.warning(self, 'تحذير', 'يرجى اختيار متربص')
                return
            query = '''
                SELECT date, session_type, reason, justification_path 
                FROM absences 
                WHERE trainee_id = ? AND date BETWEEN ? AND ?
            '''
            params = (trainee_id, date_from, date_to)
        
        elif report_type == 'جميع المتربصين':
            query = 'SELECT id, name, age, specialty, batch_id FROM trainees'
        
        elif report_type == 'جميع الغيابات':
            query = '''
                SELECT t.name, a.date, a.reason, a.session_type 
                FROM absences a 
                JOIN trainees t ON a.trainee_id = t.id 
                WHERE a.date BETWEEN ? AND ?
            '''
            params = (date_from, date_to)
        
        elif report_type == 'إحصائيات غياب شهرية':
            query = '''
                SELECT t.specialty, COUNT(a.id) as total_absences
                FROM absences a 
                JOIN trainees t ON a.trainee_id = t.id 
                WHERE a.date BETWEEN ? AND ?
                GROUP BY t.specialty
            '''
            params = (date_from, date_to)
        
        if query:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            self.current_report_data = [columns] + [list(row) for row in data]
            self.display_report(self.current_report_data)
            conn.close()
            QMessageBox.information(self, 'تم', 'تم توليد التقرير بنجاح')
    
    def display_report(self, data):
        """عرض البيانات في الجدول."""
        if not data:
            return
            
        self.table.setRowCount(len(data) - 1)
        self.table.setColumnCount(len(data[0]))
        
        # تعيين عناوين الأعمدة
        self.table.setHorizontalHeaderLabels(data[0])
        
        # تعيين البيانات
        for row_idx, row_data in enumerate(data[1:]):
            for col_idx, cell_data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))
    
    def export_pdf(self):
        """تصدير إلى PDF."""
        if not self.current_report_data:
            QMessageBox.warning(self, 'تحذير', 'لا يوجد بيانات للتصدير')
            return
            
        filename = export_to_pdf(self.current_report_data, 'تقرير نظام التكوين')
        QMessageBox.information(self, 'تم', f'تم التصدير إلى: {filename}')
    
    def export_excel(self):
        """تصدير إلى Excel."""
        if not self.current_report_data:
            QMessageBox.warning(self, 'تحذير', 'لا يوجد بيانات للتصدير')
            return
            
        filename = export_to_excel(self.current_report_data, 'تقرير نظام التكوين')
        QMessageBox.information(self, 'تم', f'تم التصدير إلى: {filename}')
    
    def print_current_report(self):
        """طباعة التقرير الحالي."""
        if not self.current_report_data:
            QMessageBox.warning(self, 'تحذير', 'لا يوجد تقرير للطباعة')
            return
            
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        
        if dialog.exec_() == QPrintDialog.Accepted:
            document = QTextDocument()
            
            # بناء محتوى HTML للتقري
            html_content = """
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, Tahoma; direction: rtl; }
                    h1 { text-align: center; }
                    table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                    th, td { border: 1px solid #000; padding: 8px; text-align: center; }
                    th { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <h1>تقرير نظام التكوين المهني</h1>
                <table>
            """
            
            # إضافة رأس الجدول
            html_content += "<tr>"
            for header in self.current_report_data[0]:
                html_content += f"<th>{header}</th>"
            html_content += "</tr>"
            
            # إضافة بيانات الجدول
            for row in self.current_report_data[1:]:
                html_content += "<tr>"
                for cell in row:
                    html_content += f"<td>{cell}</td>"
                html_content += "</tr>"
            
            html_content += """
                </table>
            </body>
            </html>
            """
            
            document.setHtml(html_content)
            document.print_(printer)
            QMessageBox.information(self, 'تم', 'تم إرسال التقرير للطباعة')