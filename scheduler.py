import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import Database
import anthropic
from config import CLAUDE_API_KEY

logger = logging.getLogger(__name__)
db = Database()


async def send_daily_reports(app):
    companies = db.get_all_registered_companies_full()
    if not companies:
        return

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    for company in companies:
        try:
            prompt = f"""أنت مستشار مالي في عالم Hostaka (محاكاة القرن العشرين).
قدّم تقريراً يومياً مختصراً جداً (5-7 أسطر فقط) لشركة:
- الاسم: {company['name']}
- الخدمة: {company['service']}
- العملة: {company['currency']}
- عدد الموظفين: {company['employees']}

التقرير يتضمن:
- الأرباح أو الخسائر المقدرة اليوم بعملة الشركة
- حالة السوق بكلمتين
- توصية واحدة مختصرة

أسلوب مهني ومختصر باللغة العربية."""

            message = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            report = message.content[0].text

            text = f"""📊 *التقرير اليومي — {company['name']}*

{report}

━━━━━━━━━━━━━━
🕐 Hostaka Stock Daily Report"""

            await app.bot.send_message(
                chat_id=company['user_id'],
                text=text,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error sending daily report for {company['name']}: {e}")


def start_scheduler(app):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_daily_reports,
        'interval',
        hours=24,
        args=[app],
        id='daily_reports'
    )
    scheduler.start()
    logger.info("✅ Daily reports scheduler started.")
