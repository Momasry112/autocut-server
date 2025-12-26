import os
import tempfile
from flask import Flask, request, jsonify
import google.generativeai as genai

# تعريف السيرفر
app = Flask(__name__)

# مفتاح جوجل
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/', methods=['POST', 'GET'])
@app.route('/<path:path>', methods=['POST', 'GET'])
def handle_request(path):
    # لو مجرد فتح للموقع
    if request.method == 'GET':
        return jsonify({"status": "Server is Running", "type": "Minimalist Version"})

    try:
        # 1. أهم خطوة: هل فيه ملف مبعوت؟
        if request.files:
            # هات أول ملف يقابلك
            file = next(iter(request.files.values()))
            
            # احفظه مؤقتاً
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
                file.save(temp.name)
                temp_path = temp.name

            # ارفعه لجوجل
            print("🎤 Uploading file...")
            myfile = genai.upload_file(temp_path)
            
            # اطلب الترجمة/التفريغ
            print("🧠 Analyzing...")
            response = model.generate_content(["Convert speech to text.", myfile])
            
            # تنظيف
            os.remove(temp_path)
            
            # إرسال الرد
            return jsonify({"response": response.text})

        # 2. لو مفيش ملف، يبقى ده اختبار اتصال (نص)
        # silent=True عشان ميضربش Error 415
        data = request.get_json(silent=True)
        if data:
            return jsonify({"response": "Connected Successfully! Send me audio now."})
            
        # لو مفيش لا ده ولا ده
        return jsonify({"response": "Server ready. Waiting for file."})

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
