import os
from flask import Flask, request
import requests

app = Flask(__name__)

PROXY_API_KEY = os.environ.get("PROXY_API_KEY")
API_URL = "https://proxyapi.ru"

@app.route("/marusia", methods=["POST"])
def marusia_skill():
    # Собираем текст из любого возможного формата запроса от Aimylogic
    user_text = ""
    if request.is_json:
        data = request.json or {}
        user_text = data.get("request", {}).get("command", "") or data.get("text", "")
    else:
        user_text = request.form.get("text", "") or request.data.decode("utf-8", errors="ignore")
    
    user_text = (user_text or "").strip()
    
    # Быстрый ответ на пустой пинг или приветствие для проверки связи
    if not user_text or user_text.lower() in ["привет", "hello"]:
        return "Привет! Твой умный ИИ Грок на связи. Задавай любой вопрос."

    if not PROXY_API_KEY:
        return "Ошибка: Не задан ключ PROXY_API_KEY в настройках сервера Render."

    headers = {
        "Authorization": f"Bearer {PROXY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "grok-beta",
        "messages": [
            {"role": "system", "content": "Ты краткий голосовой ассистент. Отвечай емко, без спецсимволов и разметки."},
            {"role": "user", "content": user_text}
        ],
        "max_tokens": 300
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.json()["choices"]["message"]["content"]
        else:
            return f"Ошибка ProxyAPI: Код {response.status_code}. Проверь баланс."
    except Exception as e:
        return f"Ошибка соединения с нейросетью: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
