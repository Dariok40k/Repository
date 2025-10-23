import telebot
from datetime import datetime, timedelta
import json
import os

# === Настройки ===
TOKEN = "8400786899:AAEJzjyVfg3T6jn2qr3EdHGW7nzu84glnug"
INACTIVITY_DAYS = 5         # сколько дней считать неактивным
DATA_FILE = "C:/Users/jxl66/Downloads/activity.json"   # где хранить активность
#CHECK_INTERVAL = 24 * 60 * 60  # интервал проверки (24 часа)
GROUP_ID = -1003147858565     # ID вашей группы (нужно указать реальный!)

bot = telebot.TeleBot(TOKEN)


# === Команда привет ===
@bot.message_handler(commands=['hi'])
def hi_command(message):
    bot.reply_to(message, "Привет!")

# === Работа с файлом ===
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# === Обновление активности пользователя ===
def update_user_activity(user):
    data = load_data()
    data[str(user.id)] = {
        "username": user.username or user.first_name,
        "last_active": datetime.utcnow().isoformat()
    }
    save_data(data)


# === Отслеживание сообщений ===
@bot.message_handler(func=lambda message: True)
def track_activity(message):
    if message.chat.type in ['group', 'supergroup']:
        update_user_activity(message.from_user)


# === Функция очистки неактивных пользователей ===
def cleanup_group(chat_id):
    bot.send_message(chat_id, f"🧹 Автоматическая очистка: проверяю неактивных более {INACTIVITY_DAYS} дней...")

    threshold_date = datetime.utcnow() - timedelta(days=INACTIVITY_DAYS)
    data = load_data()
    removed = 0

    for user_id, info in list(data.items()):
        last_active = datetime.fromisoformat(info["last_active"])
        if last_active < threshold_date:
            try:
                bot.kick_chat_member(chat_id, int(user_id))
                removed += 1
                print(f"Удалён @{info['username']} ({user_id}) — не активен с {last_active}")
                del data[user_id]
            except Exception as e:
                print(f"Ошибка при удалении {user_id}: {e}")

    save_data(data)
    bot.send_message(chat_id, f"✅ Очистка завершена. Удалено {removed} участников.")


# === Команда для ручного запуска ===
@bot.message_handler(commands=['cleanup'])
def manual_cleanup(message):
    if message.chat.type not in ['group', 'supergroup']:
        bot.reply_to(message, "Эта команда работает только в группах.")
        return

    chat_id = message.chat.id

    # Проверяем права бота
    me = bot.get_chat_member(chat_id, bot.get_me().id)
    if me.status not in ['administrator', 'creator']:
        bot.reply_to(message, "Мне нужны права администратора, чтобы удалять участников.")
        return

    cleanup_group(chat_id)

bot.polling()
    

# === Автоматическая очистка каждые 24 часа ===
#def auto_cleanup():
#    while True:
#        try:
#            cleanup_group(GROUP_ID)
#        except Exception as e:
#            print(f"Ошибка при автоочистке: {e}")