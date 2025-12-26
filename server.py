import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app) # السماح للإضافة بالاتصال

# إعداد مفتاح جوجل
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    # استخدام الاسم الرسمي عشان نتفادى خطأ 404
    model = genai.GenerativeModel('gemini-1.5-flash-001')

# أكواد التفعيل المقبولة
VALID_LICENSES = {
    "AUTOCUT-PRO-2025": True,
    "TRIAL-USER": True
}

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Server Live 🚀"})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    code = data.get('license_code')
    if code in VALID_LICENSES:
        return jsonify({"status": "success", "message": "Login Valid"})
    return jsonify({"status": "error", "message": "Invalid License"})

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # 1. التحقق من الملف
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No selected file"}), 400

        # 2. حفظ الملف مؤقتاً
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
            file.save(temp.name)
            temp_path = temp.name

        try:
            print("🎤 Uploading to Gemini...")
            myfile = genai.upload_file(temp_path)
            
            print("🧠 Generating SRT...")
            # طلبنا من الموديل إنه يرجع SRT جاهز
            response = model.generate_content([
                "Transcribe this audio. Format the output strictly as SRT (SubRip) format. Do not include any other text.", 
                myfile
            ])
            
            srt_content = response.text if response.text else "1\n00:00:00,000 --> 00:00:05,000\nNo speech detected."
            
            return jsonify({"status": "success", "srt_content": srt_content})

        except Exception as e:
            return jsonify({"status": "error", "message": f"Gemini Error: {str(e)}"})
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
