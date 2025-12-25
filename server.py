import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

MY_GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=MY_GOOGLE_API_KEY)

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
    # التحقق من الرخصة
    license_code = request.form.get('license')
    if license_code not in VALID_LICENSES:
        return jsonify({"status": "error", "message": "Unauthorized"})

    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"})

    try:
        temp_filename = "temp_audio.mp3"
        file.save(temp_filename)

        print("Uploading to Gemini...")
        uploaded_file = genai.upload_file(path=temp_filename, display_name="User Audio")
        
        # انتظار المعالجة
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(1)
            uploaded_file = genai.get_file(uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
             return jsonify({"status": "error", "message": "Google AI failed processing"})

        # --- التعديل هنا ---
        # اخترنا موديل موجود في قائمتك بالتحديد
        model = genai.GenerativeModel('gemini-2.0-flash') 
        
        prompt = """
        Transcribe this audio into Arabic (Egypt) and format it strictly as SRT.
        Output ONLY the SRT content. No markdown.
        """
        
        response = model.generate_content([prompt, uploaded_file])
        final_srt = response.text.replace("```srt", "").replace("```", "").strip()

        os.remove(temp_filename)
        return jsonify({"status": "success", "srt_content": final_srt})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)