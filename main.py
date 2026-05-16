import os
from flask import Flask, request, jsonify
import requests


app = Flask(__name__)


PROXY_API_KEY = os.environ.get("PROXY_API_KEY")
# Используем стабильный шлюз ProxyAPI
API_URL = "https://proxyapi.ru"


# Память для хранения контекста диалогов (по chat_id)
CATCH_MEMORY = {}


@app.route("/marusia", methods=["POST"])
def marusia_skill():
    user_text = ""
    chat_id = "default_user"


    # Разбираем входящий JSON от Aimylogic
    if request.is_json:
        data = request.json or {}
        user_text = data.get("request", {}).get("command", "") or data.get("text", "") or data.get("message", "")
        chat_id = str(data.get("chat_id", "") or data.get("userId", "default_user"))
    else:
        user_text = request.form.get("text", "") or request.data.decode("utf-8", errors="ignore")


    user_text = (user_text or "").strip()
    
    # Если это пустой пинг или старт — сбрасываем контекст и приветствуем
    if not user_text or user_text.lower() in ["привет", "hello", "старт", "/start"]:
        CATCH_MEMORY[chat_id] = []
        ai_text = "Привет! Твой умный ИИ Грок на связи. Задавай любой вопрос, я помню контекст нашей беседы."
        
    elif not PROXY_API_KEY:
        ai_text = "Ошибка: Не задан ключ PROXY_API_KEY в настройках сервера Render."
    else:
        if chat_id not in CATCH_MEMORY:
            CATCH_MEMORY[chat_id] = []
            
        CATCH_MEMORY[chat_id].append({"role": "user", "content": user_text})
        
        # Храним до 10 последних сообщений, чтобы не тратить лишние токены
        if len(CATCH_MEMORY[chat_id]) > 10:
            CATCH_MEMORY[chat_id] = CATCH_MEMORY[chat_id][-10:]


        headers = {
            "Authorization": f"Bearer {PROXY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Собираем системный промпт + историю чата
        messages_history = [{"role": "system", "content": "Ты краткий голосовой ассистент. Отвечай емко, без спецсимволов и разметки."}]
        messages_history.extend(CATCH_MEMORY[chat_id])


        payload = {
            "model": "gpt-4o-mini",  # Пока проверяем на супер-стабильной и дешевой модели
            "messages": messages_history,
            "max_tokens": 400
        }
        
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=25)
            if response.status_code == 200:
                # ИСПРАВЛЕНО: Добавлен индекс [0] для корректного чтения списка ответов
                ai_text = response.json()["choices"][0]["message"]["content"]
                CATCH_MEMORY[chat_id].append({"role": "assistant", "content": ai_text})
            else:
                ai_text = f"Ошибка ProxyAPI: Код {response.status_code}. Проверь баланс в личном кабинете."
                if chat_id in CATCH_MEMORY and len(CATCH_MEMORY[chat_id]) > 0:
                    CATCH_MEMORY[chat_id].pop()
        except Exception as e:
            ai_text = f"Ошибка соединения с нейросетью: {str(e)}"
            if chat_id in CATCH_MEMORY and len(CATCH_MEMORY[chat_id]) > 0:
                CATCH_MEMORY[chat_id].pop()


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
