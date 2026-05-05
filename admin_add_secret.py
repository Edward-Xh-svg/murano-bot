"""
أداة إدارية — لإضافة المعرفات السرية للجهات المؤسسة
يُشغَّل هذا الملف من سطر الأوامر من قِبل الأدمن فقط
"""
from database import Database

db = Database()

def add_secret_id():
    print("=== أداة إضافة المعرف السري ===")
    entity = input("اسم الجهة المؤسسة: ").strip()
    secret = input("المعرف السري: ").strip()
    db.add_secret_id(entity, secret)
    print(f"✅ تم إضافة المعرف '{secret}' للجهة '{entity}' بنجاح.")

if __name__ == '__main__':
    add_secret_id()
