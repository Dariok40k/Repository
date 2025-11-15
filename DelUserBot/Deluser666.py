import telebot
from datetime import datetime, timedelta, UTC
import json
import os
import time

# === Настройки ===
TOKEN = "8400786899:AAEJzjyVfg3T6jn2qr3EdHGW7nzu84glnug"
DATA_FILE = "activity.json"
INACTIVITY_DAYS = 30

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
    removed_anonymous = 0  # счётчик "пустых" пользователей

    for user_id_str, info in list(user_activity.items()):
        total_checked += 1
        uid = int(user_id_str)

        try:
            username = info.get("username", "Unknown") or "Unknown"
            last_active = datetime.fromisoformat(info["last_active"])

            # Проверка на "пустого" пользователя
            is_anonymous = (
                username.lower() in ["unknown", "deleted account", "удалённый аккаунт"] or
                username.strip() == ""
            )

            if last_active >= threshold:
                continue

            if uid in admin_ids:
                print(f"⏭ Пропущен админ @{username} ({uid})")
                continue

            # Удаляем без занесения в бан
            bot.ban_chat_member(chat_id, uid)
            bot.unban_chat_member(chat_id, uid)

            if is_anonymous:
                print(f"❌ Удалён [без имени / удалённый аккаунт] ({uid}) — не активен с {last_active}")
                removed_anonymous += 1
            else:
                print(f"❌ Удалён @{username} ({uid}) — не активен с {last_active}")

            removed += 1
            del user_activity[user_id_str]

        except telebot.apihelper.ApiTelegramException as e:
            if "user is an administrator" in str(e):
                print(f"⚠️ Нельзя удалить админа @{username} ({uid}) — Telegram запретил")
            elif "not enough rights" in str(e):
                print(f"⚠️ У бота нет прав для удаления @{username} ({uid})")
            else:
                print(f"⚠️ Ошибка при удалении {uid}: {e}")
        except Exception as e:
            print(f"⚠️ Другая ошибка при удалении {uid}: {e}")

        # Каждые 20 пользователей — отчёт
        if total_checked % 20 == 0:
            print(f"📊 Прогресс: проверено {total_checked}/{total_users} пользователей...")
            time.sleep(1)

    # Сохраняем обновлённые данные
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_activity, f, ensure_ascii=False, indent=2)

    print("\n✅ Очистка завершена!")
    print(f"📦 Удалено пользователей: {removed}/{total_users}")
    print(f"👻 Из них без имени или удалённых аккаунтов: {removed_anonymous}\n")

    bot.send_message(
        chat_id,
        f"✅ Очистка завершена.\n"
        f"Удалено: {removed} из {total_users} пользователей.\n"
        f"👻 Без имени / удалённые аккаунты: {removed_anonymous}."
    )

# === Запуск ===
bot.polling()