import os
import time
import logging
from flask import Flask, request, jsonify
import google.generativeai as genai

# --- ده السطر اللي كان ناقص وهو سبب المشكلة كلها ---
app = Flask(__name__) 
# ------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إعداد مفتاح جوجل
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("❌ GOOGLE_API_KEY not found!")
else:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

def generate_with_retry(prompt_text):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt_text)
            if response.text:
                time.sleep(4)  # حل مشكلة الـ Quota
                return response.text
        except Exception as e:
            if "429" in str(e):
                time.sleep(20)
            else:
                time.sleep(1)
    return "Error: Could not generate response."

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        return jsonify({"status": "Running"})
    
    try:
        data = request.json
        user_prompt = data.get('text') or data.get('prompt') or data.get('content')
        if not user_prompt:
            return jsonify({"error": "No text provided"}), 400
            
        result = generate_with_retry(user_prompt)
        return jsonify({"response": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)