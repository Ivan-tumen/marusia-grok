import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

PROXY_API_KEY = os.environ.get("PROXY_API_KEY")
API_URL = "https://api.proxyapi.ru/openai/v1/chat/completions"

@app.route("/marusia", methods=["POST"])
def marusia_skill():
    # Собираем текст из любого формата запроса
    user_text = ""
    if request.is_json:
        data = request.json or {}
        user_text = data.get("request", {}).get("command", "") or data.get("text", "")
    else:
        user_text = request.form.get("text", "") or request.data.decode("utf-8", errors="ignore")
    
    user_text = (user_text or "").strip()
    
    # Ответ на приветствие или пустой пинг
    if not user_text or user_text.lower() in ["привет", "hello"]:
        ai_text = "Привет! Твой умный ИИ Грок на связи. Задавай любой вопрос."
    elif not PROXY_API_KEY:
        ai_text = "Ошибка: Не задан ключ PROXY_API_KEY в настройках сервера Render."
    else:
        headers = {
            "Authorization": f"Bearer {PROXY_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Ты краткий голосовой ассистент. Отвечай емко, без спецсимволов и разметки."},
                {"role": "user", "content": user_text}
            ],
            "max_tokens": 300
        }
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=20)
            if response.status_code == 200:
                ai_text = response.json()["choices"]["message"]["content"]
            else:
                ai_text = f"Ошибка ProxyAPI: Код {response.status_code}. Проверь баланс."
        except Exception as e:
            ai_text = f"Ошибка соединения с нейросетью: {str(e)}"

    # Возвращаем строгий JSON-ответ, который устроит любую систему
    return jsonify({
        "response": {
            "text": ai_text,
            "end_session": False
        },
        "text": ai_text,
        "version": "1.0"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
