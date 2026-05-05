import anthropic
from config import CLAUDE_API_KEY
from datetime import datetime, timedelta


def get_current_game_year() -> int:
    """
    بعد 3 ساعات من الآن سيكون عام 1901 في اللعبة.
    نحسب السنة الحالية في اللعبة بناءً على هذا.
    """
    now = datetime.now()
    game_start_real = now + timedelta(hours=3)
    # كل يوم حقيقي = سنة في اللعبة (يمكن تعديل هذا)
    days_passed = (now - game_start_real).days if now > game_start_real else 0
    return 1901 + days_passed


async def analyze_company(data: dict) -> str:
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    game_year = get_current_game_year()

    prompt = f"""أنت محلل اقتصادي خبير في عالم Hostaka — محاكاة واقعية للقرن العشرين.
الآن نحن في عام {game_year} داخل اللعبة.

تم تقديم طلب لتأسيس الشركة التالية:
- اسم الشركة: {data['company_name']}
- رأسمال التأسيس: {data['capital']}
- الجهة المؤسسة: {data['founding_entity']}
- حالة الشركة: {data['stock_status']}
- اسم المؤسس: {data['founder_name']}
- الأسهم: {data['shares']}
- الخدمة: {data['service']}
- عدد الموظفين: {data['employees']}
- المساهمون: {data['shareholders']}
- العملة: {data['currency']}

قدّم تقريراً اقتصادياً شاملاً يتضمن:
1. 📊 تقدير الأرباح المتوقعة خلال العام الحالي ({game_year})
2. ⚠️ المخاطر الرئيسية في هذا القطاع خلال هذه الحقبة
3. 🌍 تأثير الموقع الجغرافي على الشركة
4. 👥 تحليل المساهمين وتأثيرهم
5. 👔 تقييم كفاءة عدد الموظفين للخدمة المقدمة
6. 📈 التوقعات للأشهر القادمة

اكتب التقرير بأسلوب مهني ومختصر، باللغة العربية، وفي حدود 300 كلمة."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text
