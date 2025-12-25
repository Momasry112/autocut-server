import os
import time
import google.generativeai as genai
import logging

# إعداد الـ Logging عشان تشوف الأخطاء في الـ Console بتاع Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. قراءة المفتاح من Environment Variables
# تأكدنا من الصورة إن الاسم عندك هو GOOGLE_API_KEY
api_key = os.getenv("GOOGLE_API_KEY")

# التحقق من وجود المفتاح
if not api_key:
    logger.error("❌ Error: GOOGLE_API_KEY not found! Please add it to Render Environment Variables.")
    # يمكن هنا رفع خطأ أو التعامل معه حسب الرغبة
    # raise ValueError("API Key not found")
else:
    # 2. تهيئة مكتبة Gemini
    genai.configure(api_key=api_key)

# 3. إعداد الموديل (تأكد إن ده الموديل اللي انت عاوز تستخدمه)
# الموديلات المتاحة: 'gemini-1.5-flash', 'gemini-pro'
MODEL_NAME = 'gemini-1.5-flash' 
model = genai.GenerativeModel(MODEL_NAME)

def generate_with_retry(prompt_text, retries=3, delay=4):
    """
    دالة كاملة لإرسال الطلب لـ Gemini مع معالجة أخطاء الـ Quota 429
    
    Args:
        prompt_text (str): النص أو البرومبت اللي هتبعاته
        retries (int): عدد محاولات الإعادة في حالة الفشل (الافتراضي 3)
        delay (int): عدد الثواني للانتظار بين الطلبات لتفادي الحظر (الافتراضي 4)
    
    Returns:
        str: النص الرد من الذكاء الاصطناعي أو None في حالة الفشل
    """
    
    for attempt in range(retries):
        try:
            logger.info(f"📤 Sending request to Gemini (Attempt {attempt + 1}/{retries})...")
            
            # إرسال الطلب
            response = model.generate_content(prompt_text)
            
            # التأكد من وصول رد سليم
            if response.text:
                logger.info("✅ Success: Received response from Gemini.")
                
                # --- النقطة الجوهرية لحل مشكلتك ---
                # الانتظار الإجباري عشان منعديش الـ Rate Limit (15 طلب في الدقيقة)
                time.sleep(delay) 
                
                return response.text
            
        except Exception as e:
            error_msg = str(e)
            
            # لو الخطأ هو 429 (تجاوزت الحد المسموح)
            if "429" in error_msg:
                wait_time = 20 # استنى 20 ثانية لو السيرفر قالك وقف
                logger.warning(f"⚠️ Quota Exceeded (429). Cooling down for {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                # لو خطأ تاني (نت مثلاً)، استنى وقت قصير وجرب تاني
                logger.error(f"❌ Error occurred: {error_msg}")
                time.sleep(2) # استنى ثانيتين بس
                
    logger.error("❌ Failed to generate content after all retries.")
    return None

# --- مثال: كيف تستخدم هذا الكود في مشروعك ---
# (الجزء ده للتوضيح، انت هتستخدم الدالة generate_with_retry جوه اللوب بتاعك)

if __name__ == "__main__":
    # تجربة بسيطة
    test_prompt = "Say hello in Arabic"
    result = generate_with_retry(test_prompt)
    print(f"Result: {result}")