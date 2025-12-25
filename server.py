import os
import time
import logging
from flask import Flask, request, jsonify
import google.generativeai as genai

# 1. إعداد السيرفر (ده الجزء اللي كان ناقص وعمل المشكلة)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. إعداد مفتاح جوجل من Environment Variables
api_key = os.getenv("GOOGLE_API_KEY")

# التأكد من وجود المفتاح
if not api_key:
    logger.error("❌ GOOGLE_API_KEY not found! Please check Render settings.")
else:
    genai.configure(api_key=api_key)

# إعداد الموديل
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. دالة الذكاء الاصطناعي الذكية (بتحل مشكلة 429)
def generate_with_retry(prompt_text):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # إرسال الطلب
            response = model.generate_content(prompt_text)
            
            # نجاح! نرجع الرد
            if response.text:
                # استنى 4 ثواني عشان منتحظرش (Quota Limit)
                time.sleep(4) 
                return response.text
                
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                # لو السيرفر زعلان، نستنى 20 ثانية ونحاول تاني
                print(f"⚠️ Quota hit (429). Cooling down... Attempt {attempt+1}")
                time.sleep(20)
            else:
                print(f"❌ Error: {error_msg}")
                time.sleep(1)
    return "Error: Could not generate response."

# 4. نقطة الاتصال الرئيسية (Endpoint)
# الإضافة بتبعت الطلبات هنا
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        return jsonify({"status": "Running", "message": "Server is up! 🚀"})

    try:
        data = request.json
        # بنستقبل النص من الإضافة (ممكن يكون اسمه text أو prompt)
        user_prompt = data.get('text') or data.get('prompt') or data.get('content')
        
        if not user_prompt:
            return jsonify({"error": "No text provided"}), 400

        # نشغل الدالة الذكية
        result = generate_with_retry(user_prompt)
        
        return jsonify({"response": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# تشغيل التطبيق
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)