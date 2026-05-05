import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler
from config import BOT_TOKEN, ADMIN_ID, GROUP_LINK
from database import init_db
from ai_analyzer import analyze_company

# إعدادات التسجيل (Logging)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# مراحل المحادثة
CHOOSING, CREATING_COMPANY, ADDING_ENTITY_NAME, ADDING_ENTITY_CODE = range(4)

# مراحل استمارة الشركة
NAME, CAPITAL, ENTITY, SECRET, STATUS, FOUNDER, SHARES, SERVICE, EMPLOYEES, SHAREHOLDERS, CURRENCY = range(4, 15)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"🏛️ أهلاً بك يا {user.first_name} في Malines Hostaka Stock!\n\n"
        "هذا البوت لإدارة شركات عالم Hostaka (القرن العشرين).\n"
        "يمكنك إنشاء شركتك وتحليلها بالذكاء الاصطناعي."
    )
    keyboard = [[KeyboardButton("🚀 ابدأ")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return CHOOSING

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏢 إنشاء شركة", callback_data="create_company")],
        [InlineKeyboardButton("ℹ️ معلومات شركة", callback_data="company_info")]
    ]
    # إذا كان المستخدم هو الأدمن، نضيف زر الإدارة
    if update.effective_user.username == "edwardmaystro":
        keyboard.append([InlineKeyboardButton("👮 إضافة جهة (أدمن)", callback_data="admin_add_entity")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر المهمة المطلوبة من القائمة أدناه:", reply_markup=reply_markup)
    return CHOOSING

# --- نظام إضافة الجهات (للأدمن فقط) ---
async def admin_start_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("👮 **وضع الإدارة:**\nيرجى إرسال اسم الجهة (مثلاً: حكومة مالينز):")
    return ADDING_ENTITY_NAME

async def admin_save_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['temp_entity_name'] = update.message.text
    await update.message.reply_text(f"تم تسجيل: {update.message.text}\nالآن أرسل المعرف السري المخصص لهذه الجهة:")
    return ADDING_ENTITY_CODE

async def admin_save_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data['temp_entity_name']
    code = update.message.text
    
    conn = sqlite3.connect('murano.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO secrets (entity_name, secret_code) VALUES (?, ?)", (name, code))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ تم الحفظ!\nالجهة: {name}\nالكود: {code}")
    return await main_menu(update, context)

# --- نظام إنشاء شركة (للمستخدمين) ---
async def start_company_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📝 **استمارة إنشاء شركة:**\n\nيرجى إرسال « اسم الشركة » :")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['c_name'] = update.message.text
    await update.message.reply_text("» رأسمال التأسيس :")
    return CAPITAL

async def get_capital(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['c_capital'] = update.message.text
    await update.message.reply_text("» الجهة المؤسسة :")
    return ENTITY

async def get_entity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['c_entity'] = update.message.text
    await update.message.reply_text("» المعرف السري للجهة المؤسسة :")
    return SECRET

async def get_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    secret_input = update.message.text
    conn = sqlite3.connect('murano.db')
    cursor = conn.cursor()
    cursor.execute("SELECT entity_name FROM secrets WHERE secret_code = ?", (secret_input,))
    result = cursor.fetchone()
    conn.close()

    if result:
        context.user_data['c_secret'] = secret_input
        context.user_data['verified_entity'] = result[0]
        await update.message.reply_text(f"✅ تم التحقق! أنت تسجل تحت جهة: {result[0]}\n\n» حالة الشركة (مدرجة في البورصة أو لا) :")
        return STATUS
    else:
        await update.message.reply_text("❌ المعرف السري غير صحيح. حاول مرة أخرى:")
        return SECRET

async def get_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['c_status'] = update.message.text
    await update.message.reply_text("» اسم المؤسس :")
    return FOUNDER

async def get_founder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['c_founder'] = update.message.text
    await update.message.reply_text("» الاسهم (إذا لا اكتب xxxx) :")
    return SHARES

async def get_shares(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['c_shares'] = update.message.text
    await update.message.reply_text("» الخدمة التي تقدمها الشركة :")
    return SERVICE

async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['c_service'] = update.message.text
    await update.message.reply_text("» عدد الموظفين :")
    return EMPLOYEES

async def get_employees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['c_employees'] = update.message.text
    await update.message.reply_text("» المساهمين :")
    return SHAREHOLDERS

async def get_shareholders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['c_shareholders'] = update.message.text
    await update.message.reply_text("» العملة :")
    return CURRENCY

async def get_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['c_currency'] = update.message.text
    user_id = update.effective_user.id
    
    await update.message.reply_text("⌛ جاري تحليل البيانات ومحاكاة القرن العشرين (1901)... انتظر قليلاً.")
    
    # تجهيز النص للذكاء الاصطناعي
    full_data = f"""
    اسم الشركة: {context.user_data['c_name']}
    رأس المال: {context.user_data['c_capital']}
    الجهة: {context.user_data['verified_entity']}
    الخدمة: {context.user_data['c_service']}
    الموظفين: {context.user_data['c_employees']}
    العملة: {context.user_data['c_currency']}
    التاريخ المحاكي: 1901
    """
    
    analysis = analyze_company(full_data)
    await update.message.reply_text(f"📊 **تقرير التحليل الأولي:**\n\n{analysis}\n\n📨 تم إرسال الطلب للإدارة للتأكد من السيولة.")
    
    # إرسال للأدمن للموافقة
    admin_notif = f"📥 طلب جديد من {user_id}:\n{full_data}\n\nللقبول أرسل: نعم_{user_id}\nللرفض أرسل: لا_{user_id}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_notif)
    
    return await main_menu(update, context)

# --- التعامل مع ردود الأدمن (نعم/لا) ---
async def admin_responses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if update.effective_user.username == "edwardmaystro":
        if text.startswith("نعم_"):
            target_id = text.split("_")[1]
            await context.bot.send_message(chat_id=target_id, text="🎉 تمت الموافقة على شركتك! تم تسجيلها في البورصة ونشرها في المجموعة.")
            await context.bot.send_message(chat_id="@YourGroupChannel", text=f"🏢 تم تسجيل شركة جديدة: {target_id}") # استبدل بمعرف مجموعتك
        elif text.startswith("لا_"):
            target_id = text.split("_")[1]
            await context.bot.send_message(chat_id=target_id, text="❌ نأسف، تم رفض طلب شركتك بسبب نقص السيولة أو أسباب إدارية.")

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.Text("🚀 ابدأ"), main_menu)],
        states={
            CHOOSING: [
                CallbackQueryHandler(start_company_creation, pattern="^create_company$"),
                CallbackQueryHandler(admin_start_add, pattern="^admin_add_entity$")
            ],
            ADDING_ENTITY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_save_name)],
            ADDING_ENTITY_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_save_final)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CAPITAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_capital)],
            ENTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_entity)],
            SECRET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_secret)],
            STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_status)],
            FOUNDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_founder)],
            SHARES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_shares)],
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            EMPLOYEES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_employees)],
            SHAREHOLDERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_shareholders)],
            CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_currency)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex(r'^(نعم_|لا_)\d+'), admin_responses))

    print("🚀 Malines Hostaka Bot is Online!")
    app.run_polling()

if __name__ == '__main__':
    main()
