import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

PROXY_API_KEY = os.environ.get("PROXY_API_KEY")
API_URL = "https://proxyapi.ru"

@app.route("/marusia", methods=["POST"])
def marusia_skill():
    # Пробуем прочитать данные как обычный текст, форму или сложный JSON от Маруси
    user_text = ""
    if request.is_json:
        data = request.json
        user_text = data.get("request", {}).get("command", "") or data.get("text", "")
    else:
        user_text = request.form.get("text", "") or request.data.decode("utf-8", errors="ignore")
    
    user_text = user_text.strip()
    
    # Если это пустой тестовый пинг от сервера
    if not user_text or user_text in ["Привет", "привет"]:
        return jsonify({
            "response": {"text": "Привет! Твой умный ИИ Грок на связи. Задавай любой вопрос.", "end_session": False},
            "version": "1.0", "session": {}
        })

    headers = {"Authorization": f"Bearer {PROXY_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "grok-beta",
        "messages": [
            {"role": "system", "content": "Ты голосовой ассистент. Отвечай кратко, емко, без лишних символов и разметки."},
            {"role": "user", "content": user_text}
        ],
        "max_tokens": 300
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=20)
        ai_text = response.json()["choices"]["message"]["content"]
    except:
        ai_text = "Произошла ошибка при обращении к искусственному интеллекту."

    return jsonify({
        "response": {"text": ai_text, "end_session": False},
        "version": "1.0", "session": {}
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
