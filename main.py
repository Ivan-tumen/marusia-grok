import os
from flask import Flask, request, jsonify
import requests


app = Flask(__name__)


PROXY_API_KEY = os.environ.get("PROXY_API_KEY")
# Возвращаем ту самую базовую ссылку, которая у вас и была в самом начале
API_URL = "https://proxyapi.ru"


# Память для контекста (хранится прямо в оперативной памяти сервера)
CATCH_MEMORY = {}


@app.route("/marusia", methods=["POST"])
def marusia_skill():
    # 1. Забираем текст ТОЧНО так же, как в вашей первой рабочей версии кода
    user_text = ""
    if request.is_json:
        data = request.json or {}
        user_text = data.get("request", {}).get("command", "") or data.get("text", "") or data.get("message", "")
    else:
        user_text = request.form.get("text", "") or request.data.decode("utf-8", errors="ignore")
    
    user_text = (user_text or "").strip()
    
    # 2. Безопасное получение ID чата (если пустой — используем общую ячейку)
    chat_id = "family_room"
    if request.is_json and request.json:
        chat_id = str(request.json.get("chat_id") or request.json.get("userId") or "family_room")


    # 3. Обработка команд сброса памяти или старта
    if not user_text or user_text.lower() in ["привет", "hello", "старт", "/start", "очисти память"]:
        CATCH_MEMORY[chat_id] = []
        ai_text = "Привет! Твой умный ИИ на связи. Я готов к диалогу и буду помнить всё, что мы обсуждаем."
        return jsonify({"text": ai_text, "response": {"text": ai_text, "end_session": False}})


    if not PROXY_API_KEY:
        return jsonify({"text": "Ошибка: Не задан токен PROXY_API_KEY."})


    # 4. Работа с историей сообщений
    if chat_id not in CATCH_MEMORY:
        CATCH_MEMORY[chat_id] = []
        
    CATCH_MEMORY[chat_id].append({"role": "user", "content": user_text})
    
    # Держим в памяти 6 последних реплик, чтобы не перегружать контекст
    if len(CATCH_MEMORY[chat_id]) > 6:
        CATCH_MEMORY[chat_id] = CATCH_MEMORY[chat_id][-6:]


    # 5. Отправка запроса к ChatGPT (gpt-4o-mini)
    headers = {
        "Authorization": f"Bearer {PROXY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages_history = [{"role": "system", "content": "Ты краткий голосовой ассистент. Отвечай емко, без спецсимволов и разметки."}]
    messages_history.extend(CATCH_MEMORY[chat_id])


    payload = {
        "model": "gpt-4o-mini",
        "messages": messages_history,
        "max_tokens": 300
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=25)
        if response.status_code == 200:
            # Берём первый элемент списка choices[0] - теперь без ошибок синтаксиса
            ai_text = response.json()["choices"][0]["message"]["content"]
            CATCH_MEMORY[chat_id].append({"role": "assistant", "content": ai_text})
        else:
            ai_text = f"Ошибка ИИ: Код {response.status_code}. Проверь баланс."
            CATCH_MEMORY[chat_id].pop() # удаляем неудачный вопрос из памяти
    except Exception as e:
        ai_text = f"Сбой сети: {str(e)}"
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
