импорт os
from flask import Flask, request, jsonify
импорт запросов


app = Flask(__name__)


PROXY_API_KEY = os.environ.get("PROXY_API_KEY")
# использовать стабильный шлюз ProxyAPI
API_URL = "https://proxyapi.ru"


# Память для хранения контекста диалогов (поchat_id)
CATCH_MEMORY = {}


@app.route("/marusia", methods=["POST"])
def marusia_skill():
    user_text = ""
    chat_id = "default_user"


    # Разбираем в будущем JSON от Aimylogic
    if request.is_json:
        data = request.json or {}
        user_text = data.get("request", "}).get("command", "") or data.get("text", "") or data.get("message", "")
        chat_id = str(data.get("chat_id", "") or data.get("userId", "default_user"))
    еще:
        user_text = request.form.get("text", "") or request.data.decode("utf-8", errors="ignore")


    user_text = (user_text or "").strip()
    
    # Если это пустой пинг или старт — сбрасываем контекст и приветствуем
    если не user_text или user_text.lower() в ["привет", "hello", "start", "/start"]:
        CATCH_MEMORY[chat_id] = []
        ai_text = "Привет! Твой умный ИИ Грок на связи. Задавай любой вопрос, я помню контекст наших бесед."
        
    elif not PROXY_API_KEY:
        ai_text = "Ошибка: Не задан ключ PROXY_API_KEY в обеспечении сервера Render."
    еще:
        если chat_id не находится в CATCH_MEMORY:
            CATCH_MEMORY[chat_id] = []
            
        CATCH_MEMORY[chat_id].append({"role": "user", "content": user_text})
        
        # Храним до 10 последних сообщений, чтобы не тратить лишние токены
        если len(CATCH_MEMORY[chat_id]) > 10:
            CATCH_MEMORY[chat_id] = CATCH_MEMORY[chat_id][-10:]


        заголовки = {
            "Авторизация": f"Предъявитель {PROXY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Собираем системный промпт + история чата
        messages_history = [{"role": "system", "content": "Ты краткий голосовой ассистент. Отвечай емко, без спецсимволов и разметок."}]
        messages_history.extend(CATCH_MEMORY[chat_id])


        полезная нагрузка = {
            "model": "gpt-4o-mini", # Пока проверяем на супер-стабильную и дешёвую модель
            "messages": messages_history,
            "max_tokens": 400
        }
        
        пытаться:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=25)
            если response.status_code == 200:
                #ИСПРАВЛЕНО: Добавлен индекс [0] для корректного чтения списка ответов
                ai_text = response.json()["choices"][0]["message"]["content"]
                CATCH_MEMORY[chat_id].append({"role": "assistant", "content": ai_text})
            еще:
                ai_text = f"Ошибка ProxyAPI: Код {response.status_code}. Проверьте баланс в личном кабинете."
                if chat_id in CATCH_MEMORY and len(CATCH_MEMORY[chat_id]) > 0:
                    CATCH_MEMORY[chat_id].pop()
        за исключением исключения как e:
            ai_text = f"Ошибка соединения с нейросетью: {str(e)}"
            if chat_id in CATCH_MEMORY and len(CATCH_MEMORY[chat_id]) > 0:
                CATCH_MEMORY[chat_id].pop()


    return jsonify({
        "ответ": {
            "текст": ai_text,
            "end_session": False
        },
        "текст": ai_text,
        "версия": "1.0"
    })


если __name__ == "__main__":
    порт = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
