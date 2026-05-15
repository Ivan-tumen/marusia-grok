import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

PROXY_API_KEY = os.environ.get("PROXY_API_KEY")
API_URL = "https://proxyapi.ru"

@app.route("/marusia", methods=["POST"])
def marusia_skill():
    data = request.json
    user_text = data.get("request", {}).get("command", "").strip()
    
    if not user_text:
        return jsonify({
            "response": {
                "text": "Привет! На связи твой умный интеллект Грок. О чем поговорим?",
                "end_session": False
            },
            "version": data["version"],
            "session": data["session"]
        })

    headers = {
        "Authorization": f"Bearer {PROXY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "grok-beta",
        "messages": [
            {"role": "system", "content": "Ты умный голосовой ассистент. Отвечай кратко, емко, без лишних символов и разметки, так как твой текст будет читаться голосом."},
            {"role": "user", "content": user_text}
        ],
        "max_tokens": 300
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=20)
        response_data = response.json()
        ai_text = response_data["choices"]["message"]["content"]
    except Exception as e:
        ai_text = "Извини, произошла ошибка при обращении к искусственному интеллекту."

    return jsonify({
        "response": {
            "text": ai_text,
            "end_session": False
        },
        "version": data["version"],
        "session": data["session"]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)