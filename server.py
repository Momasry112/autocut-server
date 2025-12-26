import os
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# إعداد مفتاح جوجل
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/', methods=['POST', 'GET'])
def index():
    # لو فتحت الرابط في المتصفح
    if request.method == 'GET':
        return jsonify({"status": "Server is Running (Text Mode) 🟢"})

    try:
        # استقبال البيانات كـ JSON
        data = request.get_json(silent=True)
        
        if not data:
            return jsonify({"error": "No data received"}), 400
            
        user_text = data.get('text')
        
        if not user_text:
            return jsonify({"response": "Connected! Write something to analyze."})

        # إرسال النص لـ Gemini
        print(f"📩 Received: {user_text}")
        response = model.generate_content(user_text)
        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
