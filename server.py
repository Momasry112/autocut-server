import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# مفتاحك من Render Environment Variables
MY_GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=MY_GOOGLE_API_KEY)

# رخص المستخدمين
VALID_LICENSES = {
    "AUTOCUT-PRO-2025": {"active": True, "plan": "pro"},
    "TEST-USER": {"active": True, "plan": "trial"}
}

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    license_code = data.get('license_code')
    if license_code in VALID_LICENSES:
        return jsonify({"status": "success", "message": "Login Successful"})
    else:
        return jsonify({"status": "error", "message": "Invalid License"})

@app.route('/analyze', methods=['POST'])
def analyze():
    # 1. التحقق من الرخصة (بتتبعت في الـ Form Data المرة دي)
    license_code = request.form.get('license')
    if license_code not in VALID_LICENSES:
        return jsonify({"status": "error", "message": "Unauthorized"})

    # 2. التحقق من وجود ملف الصوت
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"})

    try:
        # 3. حفظ الملف مؤقتاً على السيرفر
        temp_filename = "temp_audio.mp3"
        file.save(temp_filename)

        # 4. رفع الملف لـ Google Gemini AI
        print("Uploading to Gemini...")
        uploaded_file = genai.upload_file(path=temp_filename, display_name="User Audio")
        
        # انتظار المعالجة (Gemini بياخد ثواني يجهز الملف)
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(1)
            uploaded_file = genai.get_file(uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
             return jsonify({"status": "error", "message": "Google AI failed to process audio"})

        # 5. الطلب من Gemini إنشاء ملف الترجمة
        target_lang = request.form.get('language', 'Arabic')
        
        prompt = f"""
        Transcribe this audio into Arabic (Egypt) and format it strictly as SRT (SubRip Subtitle).
        Rules:
        1. No markdown code blocks (don't write ```srt).
        2. Strictly standard SRT format (Index, Timestamp, Text).
        3. Keep segments short (max 5-7 words per line) for fast-paced video style.
        4. Use Egyptian Arabic slang if detected.
        5. Output ONLY the SRT content.
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([prompt, uploaded_file])
        
        final_srt = response.text.replace("```srt", "").replace("```", "").strip()

        # تنظيف: مسح الملف من السيرفر وجوجل
        os.remove(temp_filename)
        # genai.delete_file(uploaded_file.name) # اختياري: مسح الملف من حساب جوجل

        return jsonify({
            "status": "success", 
            "srt_content": final_srt 
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)