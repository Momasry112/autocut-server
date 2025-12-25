import os
import time
import logging
from flask import Flask, request, jsonify
import google.generativeai as genai

# 1. تعريف السيرفر (ده اللي كان ناقص)
app = Flask(__name__)

# إعداد الـ Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. إعداد مفتاح جوجل
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("❌ GOOGLE_API_KEY not found! Make sure to add it in Render Environment Variables.")
else:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

def generate_with_retry(prompt_text):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # إرسال الطلب
            response = model.generate_content(prompt_text)
            if response.text:
                # انتظار 4 ثواني لتفادي الحظر
                time.sleep(4)
                return response.text
        except Exception as e:
            if "429" in str(e):
                print(f"⚠️ Quota exceeded. Retrying in 20s... (Attempt {attempt+1})")
                time.sleep(20)
            else:
                print(f"❌ Error: {e}")
                time.sleep(1)
    return "Error: Could not generate response."

@app.route('/', methods=['POST', 'GET'])
def index():
    # لو فتحت الرابط في المتصفح عادي
    if request.method == 'GET':
        return jsonify({"status": "Server is Running 🚀"})

    # لو الإضافة بعتت طلب
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        user_prompt = data.get('text') or data.get('prompt') or data.get('content')
        
        if not user_prompt:
            return jsonify({"error": "No text key found in JSON"}), 400

        result = generate_with_retry(user_prompt)
        return jsonify({"response": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
