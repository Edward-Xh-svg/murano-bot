# ai_analyzer.py
from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

def analyze_company(company_data):
    """
    تحليل الشركة بناءً على معطيات القرن العشرين وعالم Hostaka
    """
    prompt = f"""
    أنت مستشار مالي واقتصادي في عالم Hostaka لمحاكاة القرن العشرين.
    قم بتحليل بيانات الشركة التالية:
    {company_data}
    
    المطلوب تقديره وتحليله:
    1. المخاطر والأرباح المتوقعة.
    2. تأثير المساهمين والموظفين والخدمة.
    3. تأثير الجغرافيا والموقع على الأرباح.
    4. تقييم الحالة للسنة التقريبية 1901.
    
    اكتب التقرير بشكل احترافي.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"⚠️ حدث خطأ أثناء التحليل: {str(e)}"
