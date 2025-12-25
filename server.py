import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# مفتاحك السري (بيتاخد من Render)
MY_GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

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
    data = request.json
    license_code = data.get('license')
    
    if license_code not in VALID_LICENSES:
        return jsonify({"status": "error", "message": "Unauthorized"})

    language_code = data.get('language', 'ar-EG')
    lang_map = {'ar-EG': 'Arabic (Egypt)', 'en-US': 'English (US)'}
    target_lang = lang_map.get(language_code, 'Arabic')

    try:
        genai.configure(api_key=MY_GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # برومبت إنشاء SRT وهمي للتجربة (لأننا مش بنرفع ملف صوتي حقيقي لسه)
        # في المستقبل هنستقبل الملف بجد
        prompt = f"""
        Generate a sample SRT subtitle file for a 10-second video introduction in {target_lang}.
        Make it funny and engaging.
        Format: Strictly SRT format. No markdown.
        """
        
        response = model.generate_content(prompt)
        final_srt = response.text.replace("```srt", "").replace("```", "").strip()
        
        # التغيير هنا: بنرجع النص نفسه مش مسار الملف
        return jsonify({
            "status": "success", 
            "srt_content": final_srt 
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)