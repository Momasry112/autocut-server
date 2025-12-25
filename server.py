import os
import time
import logging
import tempfile
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# إعداد الـ Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداد مفتاح جوجل
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("❌ GOOGLE_API_KEY not found!")
else:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

def process_audio(file_path):
    """رفع وتحليل ملف الصوت"""
    try:
        logger.info("🎤 Uploading file to Gemini...")
        # رفع الملف لسيرفرات جوجل
        audio_file = genai.upload_file(file_path)
        
        # انتظار المعالجة (مهم جداً للصوت)
        while audio_file.state.name == "PROCESSING":
            time.sleep(1)
            audio_file = genai.get_file(audio_file.name)

        if audio_file.state.name == "FAILED":
            return "Audio processing failed."

        logger.info("🧠 Generating transcription...")
        # طلب التفريغ النصي
        response = model.generate_content([
            "Transcribe this audio file exactly as spoken. Do not add timestamps. Just the text.", 
            audio_file
        ])
        
        return response.text if response.text else "No speech detected."
    except Exception as e:
        return f"Gemini Error: {str(e)}"

# --- الجوكر: دالة تستقبل أي نوع بيانات ---
@app.route('/', defaults={'path': ''}, methods=['POST', 'GET'])
@app.route('/<path:path>', methods=['POST', 'GET'])
def catch_all(path):
    if request.method == 'GET':
        return jsonify({"status": "Server is Live 🚀"})

    try:
        logger.info(f"📥 Incoming Request. Content-Type: {request.content_type}")

        # 1. الأولوية للملفات (علاج مشكلة 415)
        if request.files:
            uploaded_file = next(iter(request.files.values())) # هات أول ملف
            if uploaded_file.filename != '':
                # حفظ الملف مؤقتاً
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
                    uploaded_file.save(temp.name)
                    temp_path = temp.name
                
                # معالجة الصوت
                result = process_audio(temp_path)
                
                # تنظيف
                os.remove(temp_path)
                return jsonify({"response": result, "status": "success"})

        # 2. لو مفيش ملف، نجرب نقرأ النص (Form Data)
        user_prompt = request.form.get('text') or request.form.get('prompt')
        
        # 3. لو مفيش Form، نجرب JSON (بحرص)
        if not user_prompt:
            json_data = request.get_json(silent=True) # silent=True بيمنع الانهيار
            if json_data:
                user_prompt = json_data.get('text') or json_data.get('prompt')

        # 4. التنفيذ
        if user_prompt:
            logger.info(f"📝 Text received: {user_prompt[:50]}...")
            response = model.generate_content(user_prompt)
            return jsonify({"response": response.text})

        # لو وصلنا هنا يبقى مفيش داتا مفهومة
        return jsonify({"response": "Connected, but no audio or text found.", "status": "success"})

    except Exception as e:
        logger.error(f"❌ Critical Error: {str(e)}")
        # ارجع JSON دايماً عشان الإضافة متضربش
        return jsonify({"error": str(e), "response": "Server Error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
