import os
import tempfile
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# إعداد مفتاح جوجل
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- التعديل هنا: ضفنا defaults={'path': ''} عشان نمنع الـ TypeError ---
@app.route('/', defaults={'path': ''}, methods=['POST', 'GET'])
@app.route('/<path:path>', methods=['POST', 'GET'])
def handle_request(path):
    # لو مجرد فتح للموقع
    if request.method == 'GET':
        return jsonify({"status": "Server is Running", "path": path})

    try:
        # 1. معالجة الملفات (الأولوية للصوت)
        if request.files:
            file = next(iter(request.files.values()))
            if file.filename == '':
                return jsonify({"error": "Empty filename"}), 400

            # حفظ مؤقت
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
                file.save(temp.name)
                temp_path = temp.name

            # رفع وتحليل
            try:
                print(f"🎤 Processing file from path: /{path}")
                myfile = genai.upload_file(temp_path)
                response = model.generate_content(["Convert this speech to text.", myfile])
                result_text = response.text if response.text else "No text found."
            except Exception as e:
                result_text = f"Gemini Error: {str(e)}"
            finally:
                os.remove(temp_path) # تنظيف الملف في كل الأحوال
            
            return jsonify({"response": result_text})

        # 2. معالجة النصوص (لو مفيش ملف)
        data = request.get_json(silent=True)
        if data:
            return jsonify({"response": "Connected! Please send audio."})
            
        # لو مفيش أي داتا
        return jsonify({"response": "Ready to receive audio.", "status": "idle"})

    except Exception as e:
        print(f"❌ Critical Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
