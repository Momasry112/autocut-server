import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# 1. مفتاحك أنت الشخصي (هيتحط على السيرفر مش عند العميل)
# في رندر هتحطه في الـ Environment Variables
MY_GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "حط_مفتاحك_الاحتياطي_هنا_مؤقتا")

# 2. قائمة الأكواد المقبولة (دي اللي هتبيعها للناس)
# ممكن بعدين نربطها بقاعدة بيانات حقيقية
VALID_LICENSES = {
    "AUTOCUT-PRO-2025": {"active": True, "plan": "pro"},
    "TRIAL-USER-123": {"active": True, "plan": "trial"},
    "AHMED-VIP": {"active": True, "plan": "unlimited"}
}

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    license_code = data.get('license_code')
    
    if license_code in VALID_LICENSES and VALID_LICENSES[license_code]['active']:
        return jsonify({
            "status": "success", 
            "message": "Login Successful",
            "plan": VALID_LICENSES[license_code]['plan']
        })
    else:
        return jsonify({"status": "error", "message": "Invalid or Expired License"})

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    license_code = data.get('license') # لازم العميل يبعت الكود مع كل طلب
    
    # تحقق من الرخصة قبل ما نكلف نفسنا ونشغل الذكاء الاصطناعي
    if license_code not in VALID_LICENSES:
        return jsonify({"status": "error", "message": "Unauthorized: Please login first."})

    # باقي كودك القديم زي ما هو...
    language_code = data.get('language', 'ar-EG')
    lang_map = {'ar-EG': 'Arabic (Egypt)', 'en-US': 'English (US)'}
    target_lang = lang_map.get(language_code, 'Arabic')

    try:
        # بنستخدم مفتاحك أنت المحفوظ في السيرفر
        genai.configure(api_key=MY_GOOGLE_API_KEY)
        
        # (هنا بنحاكي رفع الملف - في السيرفر الحقيقي لازم تستقبل الملف binary)
        # للتسهيل دلوقتي هنفترض ان الملف وصل
        # ... كود معالجة الملف ...
        
        # محاكاة الرد عشان التجربة
        return jsonify({
            "status": "success", 
            "file": "path/to/generated/captions.srt" 
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    # لازم البورت يكون ديناميكي عشان الكلاود
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)