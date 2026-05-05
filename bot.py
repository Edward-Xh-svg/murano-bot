import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from config import BOT_TOKEN, ADMIN_ID, CLAUDE_API_KEY
from database import Database
from ai_analyzer import analyze_company
from scheduler import start_scheduler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

# Conversation states
(
    WAITING_START,
    COMPANY_NAME, CAPITAL, FOUNDING_ENTITY, SECRET_ID,
    STOCK_STATUS, FOUNDER_NAME, SHARES, SERVICE,
    EMPLOYEES, SHAREHOLDERS, CURRENCY,
    ADMIN_APPROVAL
) = range(13)

WELCOME_TEXT = """
🏛️ *مرحباً بك في Malines Hostaka Stock*

هذا البوت الرسمي لإدارة الشركات في عالم *Hostaka* — محاكاة واقعية لاقتصاد القرن العشرين.

━━━━━━━━━━━━━━━━━━━━
📋 *ما يمكنك فعله هنا:*

🏢 *إنشاء شركة* — سجّل شركتك الجديدة في عالم Hostaka وابدأ رحلتك الاقتصادية

📊 *معلومات شركة* — استعرض بيانات أي شركة مسجلة في البورصة

━━━━━━━━━━━━━━━━━━━━
⚠️ *ملاحظة:* المعرف السري للجهة المؤسسة يُمنح حصرياً من إدارة *Malines*.

اضغط *ابدأ* للمتابعة 👇
"""

CREATE_COMPANY_TEXT = """
🏢 *إنشاء شركة جديدة في Hostaka*

━━━━━━━━━━━━━━━━━━━━
سيطلب منك البوت ملء استمارة تأسيس الشركة خطوة بخطوة.

📌 *تذكر:*
• المعرف السري يُمنح من إدارة Malines فقط
• بعد الإرسال، سيحلل الذكاء الاصطناعي شركتك ويُقدّر أرباحها ومخاطرها
• التحقق النهائي يتم من قِبل الإدارة

━━━━━━━━━━━━━━━━━━━━
سنبدأ الآن. أرسل اسم شركتك:

» *اسم الشركة:*
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🚀 ابدأ", callback_data="begin")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def begin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🏢 إنشاء شركة", callback_data="create_company")],
        [InlineKeyboardButton("📊 معلومات شركة", callback_data="company_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "اختر ما تريد فعله:",
        reply_markup=reply_markup
    )


async def create_company_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text(CREATE_COMPANY_TEXT, parse_mode='Markdown')
    return COMPANY_NAME


async def get_company_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['company_name'] = update.message.text.strip()
    await update.message.reply_text("» *رأسمال التأسيس:*\n\nأدخل المبلغ والعملة (مثال: 50000 فرنك)", parse_mode='Markdown')
    return CAPITAL


async def get_capital(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['capital'] = update.message.text.strip()
    await update.message.reply_text("» *الجهة المؤسسة:*\n\nما هي الجهة التي تؤسس هذه الشركة؟", parse_mode='Markdown')
    return FOUNDING_ENTITY


async def get_founding_entity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['founding_entity'] = update.message.text.strip()
    await update.message.reply_text("» *المعرف السري للجهة المؤسسة:*\n\n🔐 أدخل المعرف الذي حصلت عليه من إدارة Malines", parse_mode='Markdown')
    return SECRET_ID


async def get_secret_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    secret_id = update.message.text.strip()
    if not db.verify_secret_id(secret_id, context.user_data['founding_entity']):
        await update.message.reply_text(
            "❌ *المعرف السري غير صحيح!*\n\nتواصل مع إدارة Malines للحصول على معرفك الصحيح.",
            parse_mode='Markdown'
        )
        return SECRET_ID
    context.user_data['secret_id'] = secret_id
    await update.message.reply_text(
        "» *حالة الشركة:*\n\nهل الشركة مدرجة في البورصة؟",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ مدرجة في البورصة", callback_data="listed")],
            [InlineKeyboardButton("❌ غير مدرجة", callback_data="not_listed")]
        ])
    )
    return STOCK_STATUS


async def get_stock_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['stock_status'] = "مدرجة" if query.data == "listed" else "غير مدرجة"
    await query.message.reply_text("» *اسم المؤسس:*\n\nما هو اسم المؤسس الرئيسي؟", parse_mode='Markdown')
    return FOUNDER_NAME


async def get_founder_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['founder_name'] = update.message.text.strip()
    if context.user_data.get('stock_status') == "مدرجة":
        await update.message.reply_text(
            "» *الأسهم:*\n\nأدخل عدد الأسهم وقيمة كل سهم (مثال: 1000 سهم بـ 50 فرنك)",
            parse_mode='Markdown'
        )
    else:
        context.user_data['shares'] = 'xxxx'
        await update.message.reply_text("» *الخدمة التي تقدمها الشركة:*\n\nصف بوضوح ما تقدمه شركتك", parse_mode='Markdown')
        return SERVICE
    return SHARES


async def get_shares(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['shares'] = update.message.text.strip()
    await update.message.reply_text("» *الخدمة التي تقدمها الشركة:*\n\nصف بوضوح ما تقدمه شركتك", parse_mode='Markdown')
    return SERVICE


async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['service'] = update.message.text.strip()
    await update.message.reply_text("» *عدد الموظفين:*\n\nكم موظفاً في شركتك؟", parse_mode='Markdown')
    return EMPLOYEES


async def get_employees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['employees'] = update.message.text.strip()
    await update.message.reply_text(
        "» *المساهمون:*\n\nاذكر المساهمين وحصصهم (مثال: أحمد 40%، شركة X 60%)",
        parse_mode='Markdown'
    )
    return SHAREHOLDERS


async def get_shareholders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['shareholders'] = update.message.text.strip()
    await update.message.reply_text("» *العملة:*\n\nما هي العملة الرسمية للشركة؟ (مثال: فرنك، دولار، جنيه)", parse_mode='Markdown')
    return CURRENCY


async def get_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['currency'] = update.message.text.strip()
    data = context.user_data

    summary = f"""
📋 *ملخص الاستمارة — يرجى التحقق:*

━━━━━━━━━━━━━━━━━━━━
🏢 *اسم الشركة:* {data['company_name']}
💰 *رأسمال التأسيس:* {data['capital']}
🏛️ *الجهة المؤسسة:* {data['founding_entity']}
📈 *حالة الشركة:* {data['stock_status']}
👤 *اسم المؤسس:* {data['founder_name']}
📊 *الأسهم:* {data['shares']}
🔧 *الخدمة:* {data['service']}
👥 *عدد الموظفين:* {data['employees']}
🤝 *المساهمون:* {data['shareholders']}
💱 *العملة:* {data['currency']}
━━━━━━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(
        summary,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ تأكيد وإرسال", callback_data="confirm_submit")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
        ])
    )
    return ADMIN_APPROVAL


async def confirm_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = context.user_data
    user = update.effective_user

    await query.edit_message_text(
        "⏳ *جارٍ تحليل شركتك بالذكاء الاصطناعي...*\n\nقد يستغرق هذا بضع ثوانٍ، انتظر من فضلك.",
        parse_mode='Markdown'
    )

    analysis = await analyze_company(data)

    admin_msg = f"""
🔔 *طلب تأسيس شركة جديدة*

👤 المستخدم: @{user.username or user.first_name} (ID: {user.id})

━━━━━━━━━━━━━━━━━━━━
🏢 *{data['company_name']}*
💰 رأسمال: {data['capital']}
🏛️ الجهة: {data['founding_entity']}
📈 الحالة: {data['stock_status']}
👤 المؤسس: {data['founder_name']}
📊 الأسهم: {data['shares']}
🔧 الخدمة: {data['service']}
👥 الموظفون: {data['employees']}
🤝 المساهمون: {data['shareholders']}
💱 العملة: {data['currency']}

━━━━━━━━━━━━━━━━━━━━
🤖 *تقرير الذكاء الاصطناعي:*
{analysis}

━━━━━━━━━━━━━━━━━━━━
✅ للموافقة أرسل: نعم_{user.id}
❌ للرفض أرسل: لا_{user.id}
"""
    context.application.bot_data.setdefault('pending_companies', {})[user.id] = {
        'data': dict(data),
        'analysis': analysis,
        'user_id': user.id,
        'username': user.username or user.first_name
    }

    try:
        await context.application.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_msg,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send to admin: {e}")

    await query.message.reply_text(
        "✅ *تم إرسال طلبك بنجاح!*\n\nسيراجع الإدارة طلبك ويتحقق من السيولة.\nستُبلَّغ بالنتيجة قريباً.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ تم إلغاء العملية. أرسل /start للبدء من جديد.")
    return ConversationHandler.END


async def admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        return

    text = update.message.text.strip()
    pending = context.application.bot_data.get('pending_companies', {})

    if text.startswith("نعم_") or text.startswith("لا_"):
        parts = text.split("_")
        if len(parts) != 2:
            return
        decision, user_id_str = parts
        try:
            user_id = int(user_id_str)
        except ValueError:
            return

        if user_id not in pending:
            await update.message.reply_text("⚠️ لم يُعثر على طلب لهذا المستخدم.")
            return

        company_data = pending.pop(user_id)

        if decision == "نعم":
            db.register_company(company_data['data'], company_data['analysis'], user_id)
            # Notify the user
            await context.application.bot.send_message(
                chat_id=user_id,
                text=f"🎉 *تهانينا! تم قبول شركتك وتسجيلها رسمياً في Hostaka Stock!*\n\nستتلقى تقارير يومية عن الأرباح والخسائر.",
                parse_mode='Markdown'
            )
            # Post to group if configured
            await post_company_to_group(context, company_data)
            await update.message.reply_text(f"✅ تم قبول شركة {company_data['data']['company_name']} وتسجيلها.")
        else:
            await context.application.bot.send_message(
                chat_id=user_id,
                text="❌ *تم رفض طلب تأسيس شركتك.*\n\nالسبب: السيولة غير كافية أو بيانات غير مكتملة.\nتواصل مع إدارة Malines لمزيد من التفاصيل.",
                parse_mode='Markdown'
            )
            await update.message.reply_text(f"❌ تم رفض طلب شركة {company_data['data']['company_name']}.")


async def post_company_to_group(context, company_data):
    from config import GROUP_ID
    if not GROUP_ID:
        return
    data = company_data['data']
    analysis = company_data['analysis']
    msg = f"""
🏛️ *شركة جديدة في Hostaka Stock!*

🏢 *{data['company_name']}*
━━━━━━━━━━━━━━━━━━━━
👤 المؤسس: {data['founder_name']}
🏛️ الجهة: {data['founding_entity']}
💰 رأسمال: {data['capital']}
📈 الحالة: {data['stock_status']}
🔧 الخدمة: {data['service']}
👥 الموظفون: {data['employees']}
💱 العملة: {data['currency']}

━━━━━━━━━━━━━━━━━━━━
📊 *التحليل الاقتصادي:*
{analysis}
"""
    try:
        await context.application.bot.send_message(
            chat_id=GROUP_ID,
            text=msg,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to post to group: {e}")


async def company_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    companies = db.get_all_companies()
    if not companies:
        await query.edit_message_text("📭 لا توجد شركات مسجلة حتى الآن.")
        return
    text = "📊 *الشركات المسجلة في Hostaka Stock:*\n\n"
    for c in companies:
        text += f"🏢 *{c['name']}* — {c['status']} — {c['currency']}\n"
    await query.edit_message_text(text, parse_mode='Markdown')


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_company_callback, pattern="^create_company$")],
        states={
            COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_company_name)],
            CAPITAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_capital)],
            FOUNDING_ENTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_founding_entity)],
            SECRET_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_secret_id)],
            STOCK_STATUS: [CallbackQueryHandler(get_stock_status, pattern="^(listed|not_listed)$")],
            FOUNDER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_founder_name)],
            SHARES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_shares)],
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            EMPLOYEES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_employees)],
            SHAREHOLDERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_shareholders)],
            CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_currency)],
            ADMIN_APPROVAL: [
                CallbackQueryHandler(confirm_submit, pattern="^confirm_submit$"),
                CallbackQueryHandler(cancel_callback, pattern="^cancel$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_callback, pattern="^cancel$")],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(begin_callback, pattern="^begin$"))
    app.add_handler(CallbackQueryHandler(company_info_callback, pattern="^company_info$"))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(int(ADMIN_ID)),
        admin_response
    ))

    start_scheduler(app)

    logger.info("🚀 Malines Hostaka Stock Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
