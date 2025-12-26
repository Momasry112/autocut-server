import os
import tempfile
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# إعداد مفتاح جوجل
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    # بعد تحديث المكتبة، الاسم ده هيشتغل تمام
    model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/', defaults={'path': ''}, methods=['POST', 'GET'])
@app.route('/<path:path>', methods=['POST', 'GET'])
def handle_request(path):
    if request.method == 'GET':
        return jsonify({"status": "Server is Running 🚀"})

    try:
        # 1. استقبال ملف الصوت (الأولوية هنا)
        if request.files:
            file = next(iter(request.files.values()))
            if file.filename == '':
                return jsonify({"error": "No selected file"}), 400

            # حفظ مؤقت
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
                file.save(temp.name)
                temp_path = temp.name

            # رفع وتحليل
            try:
                print(f"🎤 Processing audio...")
                myfile = genai.upload_file(temp_path)
                
                # إرسال الأمر للموديل
                response = model.generate_content(["Transcribe this audio file to text.", myfile])
                result_text = response.text if response.text else "No text found."
            except Exception as e:
                # لو حصل خطأ في الموديل نرجعه عشان نشوفه
                result_text = f"Gemini Error: {str(e)}"
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            return jsonify({"response": result_text})

        # 2. لو مفيش ملف
        return jsonify({"response": "Connected! Please upload an audio file."})

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
