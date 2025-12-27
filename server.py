import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# 1. مفتاح Gemini API (تأكد من تغييره بمفتاحك السري)
api_key = os.environ.get("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY_HERE")
genai.configure(api_key=api_key)

# نستخدم موديل فلاش لأنه سريع جداً ودقيق في التوقيت
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/analyze', methods=['POST'])
def analyze_audio():
    try:
        # 1. استقبال الملف من الإضافة
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No audio file uploaded"}), 400
        
        file = request.files['file']
        
        # 2. حفظ مؤقت
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
            file.save(temp.name)
            temp_path = temp.name

        print("🎤 Processing audio with Gemini...")

        # 3. إرسال لجوجل للتحليل
        myfile = genai.upload_file(temp_path)
        
        # الأمر السحري للحصول على SRT دقيق
        prompt = "Transcribe this audio file into Arabic (Egypt). Format the output strictly as a valid SRT (SubRip) file. Ensure timestamps match exactly."
        
        response = model.generate_content([prompt, myfile])
        
        # تنظيف الملف المؤقت
        os.remove(temp_path)

        # 4. إرسال النتيجة للإضافة
        return jsonify({
            "status": "success", 
            "srt_content": response.text
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
