import sqlite3

def init_db():
    """
    تهيئة قاعدة البيانات وإنشاء الجداول اللازمة لنظام Malines Hostaka.
    """
    # الاتصال بقاعدة البيانات (سيتم إنشاؤها إذا لم تكن موجودة)
    conn = sqlite3.connect('murano.db')
    cursor = conn.cursor()

    # 1. جدول الشركات: لتخزين بيانات استمارة الأعضاء وحالة الموافقة
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,           -- معرف التليجرام للمالك
            name TEXT,                 -- اسم الشركة
            capital TEXT,              -- رأس المال
            founder_entity TEXT,       -- الجهة المؤسسة (التي يدخلها المستخدم)
            verified_entity TEXT,      -- اسم الجهة الفعلي المرتبط بالمعرف السري
            secret_id TEXT,            -- المعرف السري المستخدم
            status TEXT,               -- حالة الشركة (مدرجة أم لا)
            founder_name TEXT,         -- اسم المؤسس
            shares TEXT,               -- عدد الأسهم
            service TEXT,              -- نوع الخدمة
            employees TEXT,            -- عدد الموظفين
            shareholders TEXT,         -- المساهمين
            currency TEXT,             -- العملة المستخدمة
            approval_status TEXT DEFAULT 'pending' -- حالة الطلب (pending, approved, rejected)
        )
    ''')

    # 2. جدول المعرفات السرية: لربط الأكواد بالجهات الرسمية (إدارة مالينز)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_name TEXT,          -- اسم الجهة (مثلاً: حكومة مالينز)
            secret_code TEXT UNIQUE    -- المعرف السري (يجب أن يكون فريداً)
        )
    ''')

    # حفظ التغييرات وإغلاق الاتصال
    conn.commit()
    conn.close()
    print("✅ تم تهيئة قاعدة بيانات Murano بنجاح.")

if __name__ == '__main__':
    init_db()
