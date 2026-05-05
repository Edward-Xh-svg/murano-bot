# bot.py
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, ADMIN_ID, GROUP_LINK
from database import init_db
from ai_analyzer import analyze_company

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# قاموس لتخزين بيانات المستخدمين المؤقتة أثناء إنشاء الشركة
user_data_temp = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # رسالة الترحيب والتعريف
    welcome_text = (
        f"أهلاً بك يا {user.first_name} في بوت Malines Hostaka Stock!\n\n"
        "هذا البوت مخصص لإدارة الشركات في عالم Hostaka الاقتصادي (القرن العشرين).\n"
        "استخدم الأزرار أدناه للبدء:"
    )
    
    # الأزرار الرئيسية
    keyboard = [
        [KeyboardButton("🚀 ابدأ")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_start_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🚀 ابدأ":
        keyboard = [
            [InlineKeyboardButton("🏢 إنشاء شركة", callback_data="create_company")],
            [InlineKeyboardButton("ℹ️ معلومات شركة", callback_data="company_info")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("اختر أحد الخيارات التالية:", reply_markup=reply_markup)
        
    # التعامل مع قبول أو رفض الأدمن
    elif update.effective_user.username == "edwardmaystro":
        if text.startswith("نعم_"):
            user_id = text.split("_")[1]
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 تهانينا! تمت الموافقة على طلب شركتك وتأكيد السيولة من قبل الإدارة."
            )
            await context.bot.send_message(
                chat_id="-1001234567890", # أو GROUP_LINK
                text="🏢 تم إدراج شركة جديدة في النظام."
            )
            await update.message.reply_text("تم قبول العملية وتسجيل الشركة.")
        elif text.startswith("لا_"):
            user_id = text.split("_")[1]
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ نأسف لإعلامك بأنه تم رفض طلب شركتك."
            )
            await update.message.reply_text("تم رفض العملية.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "create_company":
        user_data_temp[query.from_user.id] = {"step": "name"}
        await query.message.reply_text(
            "📝 **استمارة إنشاء شركة:**\n\n"
            "يرجى إدخال اسم الشركة الجديد:"
        )
    elif query.data == "company_info":
        await query.message.reply_text("أدخل اسم الشركة التي تريد البحث عن معلوماتها:")

async def handle_company_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data_temp:
        return
    
    text = update.message.text
    step = user_data_temp[user_id]["step"]
    
    if step == "name":
        user_data_temp[user_id]["name"] = text
        user_data_temp[user_id]["step"] = "capital"
        await update.message.reply_text(" » رأسمال التأسيس :")
        
    elif step == "capital":
        user_data_temp[user_id]["capital"] = text
        user_data_temp[user_id]["step"] = "founder_entity"
        await update.message.reply_text(" » الجهة المؤسسة :")
        
    elif step == "founder_entity":
        user_data_temp[user_id]["founder_entity"] = text
        user_data_temp[user_id]["step"] = "secret_id"
        await update.message.reply_text(" » المعرف السري للجهة المؤسسة (الذي استلمته من الإدارة) :")
        
    elif step == "secret_id":
        user_data_temp[user_id]["secret_id"] = text
        
        # التحقق من المعرف السري في قاعدة البيانات
        conn = sqlite3.connect('murano.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM secrets WHERE secret_code = ?", (text,))
        res = cursor.fetchone()
        conn.close()
        
        if not res:
            await update.message.reply_text("❌ المعرف السري غير صحيح. يرجى إعادة المحاولة أو طلب المعرف من الإدارة.")
            return
            
        user_data_temp[user_id]["step"] = "status"
        await update.message.reply_text(" » حالة الشركة (مدرجة في البورصة أو لا) :")
        
    elif step == "status":
        user_data_temp[user_id]["status"] = text
        user_data_temp[user_id]["step"] = "founder_name"
        await update.message.reply_text(" » اسم المؤسس :")
        
    elif step == "founder_name":
        user_data_temp[user_id]["founder_name"] = text
        user_data_temp[user_id]["step"] = "shares"
        await update.message.reply_text(" » الاسهم (في حالة الشركة مدرجة، إذا لا اكتب xxxx) :")
        
    elif step == "shares":
        user_data_temp[user_id]["shares"] = text
        user_data_temp[user_id]["step"] = "service"
        await update.message.reply_text(" » الخدمة التي تقدمها الشركة :")
        
    elif step == "service":
        user_data_temp[user_id]["service"] = text
        user_data_temp[user_id]["step"] = "employees"
        await update.message.reply_text(" » عدد الموظفين :")
        
    elif step == "employees":
        user_data_temp[user_id]["employees"] = text
        user_data_temp[user_id]["step"] = "shareholders"
        await update.message.reply_text(" » المساهمين :")
        
    elif step == "shareholders":
        user_data_temp[user_id]["shareholders"] = text
        user_data_temp[user_id]["step"] = "currency"
        await update.message.reply_text(" » العملة :")
        
    elif step == "currency":
        user_data_temp[user_id]["currency"] = text
        
        # إنهاء الاستمارة
        data_summary = user_data_temp[user_id]
        await update.message.reply_text("⏳ جاري التحقق من الخدمة وتوليد التحليل والمخاطر باستخدام Gemini... (قد يستغرق 3 ساعات لمحاكاة عام 1901)")
        
        analysis = analyze_company(str(data_summary))
        await update.message.reply_text(f"📊 نتائج التحليل:\n\n{analysis}\n\n⏳ تم إرسال الطلب للأدمن للتأكد من السيولة.")
        
        # إشعار للأدمن
        try:
            await context.bot.send_message(
                chat_id="123456789", # رقم الإدارة
                text=f"طلب جديد من {user_id} لإنشاء شركة:\nالبيانات: {data_summary}\n\nللقبول أرسل: نعم_{user_id}\nللرفض أرسل: لا_{user_id}"
            )
        except Exception:
            pass
        
        del user_data_temp[user_id] # إفراغ البيانات

def main():
    init_db()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_start_button))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_company_creation))
    
    print("🚀 البوت يعمل الآن...")
    application.run_polling()

if __name__ == '__main__':
    main()
