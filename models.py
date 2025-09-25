# models.py
import sqlite3
from database import get_connection
from datetime import datetime

class Trainee:
    """نموذج المتربص مع CRUD."""
    
    @staticmethod
    def create(name, age, specialty, photo_path='', batch_id=1, join_date=None):
        """إضافة متربص جديد."""
        if join_date is None:
            join_date = datetime.now().strftime('%Y-%m-%d')
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trainees (name, age, specialty, photo_path, batch_id, join_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, age, specialty, photo_path, batch_id, join_date))
        trainee_id = cursor.lastrowid
        conn.commit()
        conn.close()
        from utils.security import log_activity
        log_activity('admin', f'إضافة متربص: {name}')
        return trainee_id
    
    @staticmethod
    def read_all():
        """قراءة جميع المتربصين."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trainees')
        return cursor.fetchall()
    
    @staticmethod
    def update(id, **kwargs):
        """تعديل متربص."""
        fields = ', '.join([f"{k}=?" for k in kwargs])
        values = list(kwargs.values()) + [id]
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f'UPDATE trainees SET {fields} WHERE id=?', values)
        conn.commit()
        conn.close()
        from utils.security import log_activity
        log_activity('admin', f'تعديل متربص ID: {id}')
    
    @staticmethod
    def delete(id):
        """حذف متربص."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM trainees WHERE id=?', (id,))
        conn.commit()
        conn.close()
        from utils.security import log_activity
        log_activity('admin', f'حذف متربص ID: {id}')
    
    @staticmethod
    def search(name):
        """بحث حسب الاسم."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trainees WHERE name LIKE ?', (f'%{name}%',))
        return cursor.fetchall()

# نماذج أخرى مشابهة (مختصرة للاختصار، يمكن تكرار النمط)
class Absence:
    @staticmethod
    def create(trainee_id, date, session_type='full_day', reason='', justification_path=''):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO absences (trainee_id, date, session_type, reason, justification_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (trainee_id, date, session_type, reason, justification_path))
        conn.commit()
        conn.close()
        from utils.security import log_activity
        log_activity('admin', f'تسجيل غياب لمتربص ID: {trainee_id}')
    
    @staticmethod
    def read_by_trainee(trainee_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM absences WHERE trainee_id=?', (trainee_id,))
        return cursor.fetchall()

class Document:
    @staticmethod
    def create(trainee_id, doc_type, file_path):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO documents (trainee_id, doc_type, file_path)
            VALUES (?, ?, ?)
        ''', (trainee_id, doc_type, file_path))
        conn.commit()
        conn.close()
        from utils.security import log_activity
        log_activity('admin', f'إضافة وثيقة لمتربص ID: {trainee_id}')

class Batch:
    @staticmethod
    def create(name, period='سداسي أول'):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO batches (name, period) VALUES (?, ?)', (name, period))
        return cursor.lastrowid

class Schedule:
    @staticmethod
    def create(day, time_slot, subject, batch_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO schedules (day, time_slot, subject, batch_id)
            VALUES (?, ?, ?, ?)
        ''', (day, time_slot, subject, batch_id))
        conn.commit()
        conn.close()

class Promotion:
    @staticmethod
    def create(batch_id, from_period, to_period, minutes_path=''):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO promotions (batch_id, from_period, to_period, minutes_path)
            VALUES (?, ?, ?, ?)
        ''', (batch_id, from_period, to_period, minutes_path))
        conn.commit()
        conn.close()

class DisciplinaryAction:
    @staticmethod
    def create(trainee_id, action_type, description='', pdf_path=''):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO disciplinary_actions (trainee_id, action_type, description, pdf_path)
            VALUES (?, ?, ?, ?)
        ''', (trainee_id, action_type, description, pdf_path))
        conn.commit()
        conn.close()

# وظائف عامة للتقارير
def generate_report(query, params=(), format='pdf'):
    """توليد تقرير (مثال بسيط، يُستخدم في reports_window)."""
    from utils.exporter import export_to_pdf, export_to_excel
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = cursor.fetchall()
    if format == 'pdf':
        return export_to_pdf(data, 'تقرير عام')
    else:
        return export_to_excel(data, 'تقرير عام')
# في models.py، أضف/حدث:

def generate_report(query, params=(), format='pdf'):
    """توليد تقرير (محدث لدعم header)."""
    from utils.exporter import export_to_pdf, export_to_excel
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = cursor.fetchall()
    # افترض header من الاستعلام أو أضف يدويًا
    if format == 'pdf':
        return export_to_pdf([[]] + [list(row) for row in data], 'تقرير')  # header فارغ؛ حدث حسب الحاجة
    else:
        return export_to_excel([[]] + [list(row) for row in data], 'تقرير')

# لـ Batch، أضف read_all
class Batch:
    # ... (الكود السابق)
    @staticmethod
    def read_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM batches')
        data = cursor.fetchall()
        conn.close()
        return data

# كرر للنماذج الأخرى إذا لزم (مثل Promotion.read_all()، إلخ.)
# في models.py، أضف/حدث:

def generate_report(query, params=(), format='pdf'):
    """توليد تقرير (محدث لدعم header)."""
    from utils.exporter import export_to_pdf, export_to_excel
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = cursor.fetchall()
    # افترض header من الاستعلام أو أضف يدويًا
    if format == 'pdf':
        return export_to_pdf([[]] + [list(row) for row in data], 'تقرير')  # header فارغ؛ حدث حسب الحاجة
    else:
        return export_to_excel([[]] + [list(row) for row in data], 'تقرير')

# لـ Batch، أضف read_all
class Batch:
    # ... (الكود السابق)
    @staticmethod
    def read_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM batches')
        data = cursor.fetchall()
        conn.close()
        return data

# كرر للنماذج الأخرى إذا لزم (مثل Promotion.read_all()، إلخ.)
# models.py - الإضافات والتعديلات النهائية
import sqlite3
from database import get_connection
from datetime import datetime

# إضافة الدوال المفقودة للأنماط الأخرى
class Batch:
    @staticmethod
    def create(name, period='سداسي أول'):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO batches (name, period) VALUES (?, ?)', (name, period))
        batch_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return batch_id
    
    @staticmethod
    def read_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM batches')
        data = cursor.fetchall()
        conn.close()
        return data

class Schedule:
    @staticmethod
    def create(day, time_slot, subject, batch_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO schedules (day, time_slot, subject, batch_id)
            VALUES (?, ?, ?, ?)
        ''', (day, time_slot, subject, batch_id))
        conn.commit()
        conn.close()

class Promotion:
    @staticmethod
    def create(batch_id, from_period, to_period, minutes_path=''):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO promotions (batch_id, from_period, to_period, minutes_path)
            VALUES (?, ?, ?, ?)
        ''', (batch_id, from_period, to_period, minutes_path))
        conn.commit()
        conn.close()

class DisciplinaryAction:
    @staticmethod
    def create(trainee_id, action_type, description='', pdf_path=''):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO disciplinary_actions (trainee_id, action_type, description, pdf_path)
            VALUES (?, ?, ?, ?)
        ''', (trainee_id, action_type, description, pdf_path))
        conn.commit()
        conn.close()

# تحسين دالة generate_report
def generate_report(query, params=(), format='pdf', title='تقرير'):
    """توليد تقرير بمستوى محسن."""
    from utils.exporter import export_to_pdf, export_to_excel
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = cursor.fetchall()
    
    # الحصول على أسماء الأعمدة
    column_names = [description[0] for description in cursor.description]
    
    if format == 'pdf':
        return export_to_pdf([column_names] + [list(row) for row in data], title)
    else:
        return export_to_excel([column_names] + [list(row) for row in data], title)