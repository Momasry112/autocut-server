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

def generate_from_text(prompt_text):
    """ معالجة النصوص العادية """
    try:
        response = model.generate_content(prompt_text)
        return response.text if response.text else "No response generated."
    except Exception as e:
        return f"Error: {str(e)}"

def process_audio_file(file_storage):
    """ معالجة ملفات الصوت باستخدام Gemini """
    try:
        # 1. حفظ الملف مؤقتاً
        suffix = os.path.splitext(file_storage.filename)[1] # .mp3
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            file_storage.save(temp_file.name)
            temp_path = temp_file.name

        logger.info(f"🎤 Processing audio file: {file_storage.filename}")

        # 2. رفع الملف لـ Gemini
        myfile = genai.upload_file(temp_path)
        
        # 3. الطلب من Gemini تحليل الصوت
        # (يمكنك تعديل البرومبت هنا حسب رغبتك: ترجمة، تلخيص، تفريغ)
        response = model.generate_content(["Please transcribe this audio file accurately.", myfile])
        
        # 4. تنظيف الملفات
        os.remove(temp_path)
        
        return response.text if response.text else "No transcription generated."

    except Exception as e:
        logger.error(f"❌ Audio Error: {str(e)}")
        return f"Audio processing error: {str(e)}"

# --- الجوكر: دالة ترد على أي رابط وأي نوع بيانات ---
@app.route('/', defaults={'path': ''}, methods=['POST', 'GET'])
@app.route('/<path:path>', methods=['POST', 'GET'])
def catch_all(path):
    logger.info(f"📥 Request to path: /{path}")

    if request.method == 'GET':
        return jsonify({"status": "Server Running", "path": path})

    try:
        # الحالة 1: استلام ملف (MP3/WAV)
        if request.files:
            # هات أول ملف مبعوت
            file = next(iter(request.files.values()))
            if file:
                logger.info("📁 File received!")
                result = process_audio_file(file)
                return jsonify({"response": result, "status": "success"})

        # الحالة 2: استلام JSON (نص)
        if request.is_json:
            data = request.json
            user_prompt = data.get('text') or data.get('prompt') or data.get('content')
            if user_prompt:
                logger.info("📝 Text received!")
                result = generate_from_text(user_prompt)
                return jsonify({"response": result, "status": "success"})

        # حالة احتياطية: لو البيانات مبعوطة Form Data مش JSON
        if request.form:
            user_prompt = request.form.get('text') or request.form.get('prompt')
            if user_prompt:
                result = generate_from_text(user_prompt)
                return jsonify({"response": result, "status": "success"})

        return jsonify({"response": "Connected but no content found", "status": "success"})

    except Exception as e:
        logger.error(f"❌ Critical Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
