import telebot
from datetime import datetime, timedelta, UTC
import json
import os
import time

# === Настройки ===
TOKEN = "8400786899:AAEJzjyVfg3T6jn2qr3EdHGW7nzu84glnug"
DATA_FILE = "activity.json"
INACTIVITY_DAYS = 60

bot = telebot.TeleBot(TOKEN)

# === Загрузка данных ===
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        user_activity = json.load(f)
else:
    user_activity = {}

print("✅ Бот загружен и готов к очистке...\n")

# === Команда очистки ===
@bot.message_handler(commands=['cleanup'])
def cleanup(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Проверяем, имеет ли пользователь права
    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status not in ['creator', 'administrator']:
            bot.send_message(chat_id, "🚫 Только администратор или владелец может запускать очистку.")
            print(f"⛔ Пользователь {user_id} попытался запустить очистку без прав.\n")
            return
    except Exception as e:
        print(f"❌ Ошибка при проверке прав пользователя: {e}\n")
        bot.send_message(chat_id, "Не удалось проверить права доступа.")
        return

    print(f"🧹 Запуск очистки в чате {chat_id} от пользователя {user_id}...\n")

    # Получаем список админов
    try:
        admins = bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in admins]
        print(f"🔐 Найдено админов: {len(admin_ids)}\n")
    except Exception as e:
        print(f"❌ Ошибка при получении админов: {e}\n")
        bot.send_message(chat_id, "Не удалось получить список админов.")
        return

    threshold = datetime.now(UTC) - timedelta(days=INACTIVITY_DAYS)
    removed = 0
    total_checked = 0
    total_users = len(user_activity)

    for user_id_str, info in list(user_activity.items()):
        total_checked += 1
        uid = int(user_id_str)

        try:
            last_active = datetime.fromisoformat(info["last_active"])

            if last_active >= threshold:
                continue

            if uid in admin_ids:
                print(f"⏭ Пропущен админ @{info['username']} ({uid})")
                continue

            # Удаляем без бана: сначала ban, затем unban
            bot.ban_chat_member(chat_id, uid)
            bot.unban_chat_member(chat_id, uid)
            print(f"❌ Удалён @{info['username']} ({uid}) — не активен с {last_active}")
            removed += 1
            del user_activity[user_id_str]

        except telebot.apihelper.ApiTelegramException as e:
            if "user is an administrator" in str(e):
                print(f"⚠️ Нельзя удалить админа @{info['username']} ({uid}) — Telegram запретил")
            elif "not enough rights" in str(e):
                print(f"⚠️ У бота нет прав для удаления @{info['username']} ({uid})")
            else:
                print(f"⚠️ Ошибка при удалении {uid}: {e}")
        except Exception as e:
            print(f"⚠️ Другая ошибка при удалении {uid}: {e}")

        # Каждые 20 пользователей — небольшой отчёт
        if total_checked % 20 == 0:
            print(f"📊 Прогресс: проверено {total_checked}/{total_users} пользователей...")
            time.sleep(1)  # чтобы Telegram не ограничил запросы

    # Сохраняем обновлённые данные
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_activity, f, ensure_ascii=False, indent=2)

    print("\n✅ Очистка завершена!")
    print(f"📦 Удалено пользователей: {removed}/{total_users}\n")

    bot.send_message(chat_id, f"✅ Очистка завершена.\nУдалено: {removed} из {total_users} пользователей.")

# === Запуск ===
bot.polling()