import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# 1. إعداد مفتاح جوجل (استخدمنا المفتاح اللي انت بعته)
# في الوضع الحقيقي، يفضل تحطه في Environment Variables في Render عشان الأمان
api_key = os.environ.get("GOOGLE_API_KEY", "AIzaSyA9_BQ92YKj0GB4vwfk50WS_ZvR2IGLMto")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash-001') # الموديل الرسمي

# 2. قاعدة بيانات التراخيص (وهمية)
VALID_LICENSES = {
    "AUTOCUT-PRO-2025": True,
    "TRIAL-USER": True,
    "admin": True 
}

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Server Live 🟢", "model": "Gemini 1.5 Flash"})

# دالة تسجيل الدخول
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    code = data.get('license_code')
    
    # أي كود هتكتبه هيتقبل عشان التجربة، أو استخدم الأكواد اللي فوق
    if code: 
        return jsonify({"status": "success", "message": "License Valid", "user_type": "Pro"})
    
    return jsonify({"status": "error", "message": "Invalid License"})

# دالة التحليل (شغالة بمفتاحك الجديد)
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
            file.save(temp.name)
            temp_path = temp.name

        print("🎤 Analyzing audio with YOUR API Key...")
        myfile = genai.upload_file(temp_path)
        response = model.generate_content(["Convert this audio to SRT format.", myfile])
        
        os.remove(temp_path)
        return jsonify({"status": "success", "srt_content": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
