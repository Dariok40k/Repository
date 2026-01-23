#!/usr/bin/env python3
# bot_combined.py
# Единый бот для сбора активности и очистки чата на хостинге


import telebot
import asyncio
from pyrogram import Client
from datetime import datetime, timedelta, timezone
import json
import os
import time
import logging
from logging.handlers import RotatingFileHandler

# === НАСТРОЙКИ ===
TOKEN = "8400786899:AAEJzjyVfg3T6jn2qr3EdHGW7nzu84glnug"
GROUP_ID = -1002361725921  # ID группы для очистки и сбора


API_ID = 29664255
API_HASH = "89a43fab6a5944a1da7e646318a7b3e9"


DATA_FILE = "activity.json"
INACTIVITY_DAYS = 30


COLLECTOR_INTERVAL = 86400      # 24 часа (в секундах)
BOT_POLLING_INTERVAL = 60       # 1 минута (в секундах)


# === ЛОГИРОВАНИЕ ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        RotatingFileHandler("logs/bot.log", maxBytes=5*1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === ПРОВЕРКА И УСТАНОВКА ЗАВИСИМОСТЕЙ ===
def check_dependencies():
    try:
        import telebot
        import pyrogram
        logger.info("✅ Все зависимости установлены.")
    except ImportError as e:
        logger.error(f"❌ Не хватает библиотеки: {e}. Установите через pip:")
        logger.error("pip install pyTelegramBotAPI pyrogram")
        exit(1)

check_dependencies()

# === ЗАГРУЗКА ДАННЫХ ===
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Ошибка чтения {DATA_FILE}: {e}")
            return {}
    else:
        logger.warning(f"⚠️ Файл {DATA_FILE} не найден. Будет создан при сборе данных.")
        return {}

user_activity = load_data()

# === СБОРЩИК АКТИВНОСТИ (Pyrogram) ===
async def collect_activity():
    logger.info("🚀 Запущен сборщик активности...")
    app = Client("collector_session", api_id=API_ID, api_hash=API_HASH)
    
    user_activity_new = {}
    default_date = datetime(2000, 1, 1, tzinfo=timezone.utc).isoformat()

    try:
        async with app:
            logger.info("Получаем участников группы...")
            count_members = 0
            async for member in app.get_chat_members(GROUP_ID):
                user = member.user
                if user.is_bot:
                    continue
                uid = str(user.id)
                username = user.username or user.first_name or "Unknown"
                user_activity_new[uid] = {
                    "username": username,
                    "last_active": default_date
                }
                count_members += 1
                if count_members % 100 == 0:
                    logger.info(f"Обработано участников: {count_members}")

            logger.info(f"Всего участников: {count_members}")

            logger.info("Сканируем историю сообщений...")
            count_messages = 0
            async for message in app.get_chat_history(GROUP_ID):
                count_messages += 1
                if message.from_user:
                    uid = str(message.from_user.id)
                    last_active = message.date.astimezone(timezone.utc).isoformat()
                    if uid in user_activity_new:
                        if last_active > user_activity_new[uid]["last_active"]:
                            user_activity_new[uid]["last_active"] = last_active


                if count_messages % 500 == 0:
                    logger.info(f"Обработано сообщений: {count_messages}")


            logger.info(f"Обработка завершена. Сообщений: {count_messages}")

    except Exception as e:
        logger.error(f"❌ Ошибка сборщика: {e}")
        return

    # Сохраняем данные
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(user_activity_new, f, ensure_ascii=False, indent=2)
        logger.info(f"Данные сохранены в {DATA_FILE}")
        global user_activity
        user_activity = user_activity_new
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения {DATA_FILE}: {e}")


# === БОТ‑ОЧИСТИТЕЛЬ (telebot) ===
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['cleanup'])
def cleanup(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Проверка прав
    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status not in ['creator', 'administrator']:
            bot.send_message(chat_id, "🚫 Только администратор может запускать очистку.")
            logger.warning(f"Пользователь {user_id} без прав попытался запустить очистку.")
            return
    except Exception as e:
        logger.error(f"Ошибка проверки прав: {e}")
        bot.send_message(chat_id, "Не удалось проверить права.")
        return

    logger.info(f"Запуск очистки в чате {chat_id} от пользователя {user_id}...")

    # Получаем админов
    try:
        admins = bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in admins]
        logger.info(f"Найдено админов: {len(admin_ids)}")
    except Exception as e:
        logger.error(f"Ошибка получения админов: {e}")
        bot.send_message(chat_id, "Не удалось получить список админов.")
        return

    threshold = datetime.now(timezone.utc) - timedelta(days=INACTIVITY_DAYS)
    removed = 0
    total_checked = 0
    total_users = len(user_activity)
    removed_anonymous = 0

    for user_id_str, info in list(user_activity.items()):
        total_checked += 1
        uid = int(user_id_str)

        try:
            username = info.get("username", "Unknown") or "Unknown"
            last_active = datetime.fromisoformat(info["last_active"])

            is_anonymous = (
                username.lower() in ["unknown", "deleted account", "удалённый аккаунт"] or
                username.strip() == ""
            )

            if last_active >= threshold:
                continue

            if uid in admin_ids:
                logger.info(f"Пропущен админ @{username} ({uid})")
                continue

            # Удаляем и сразу разблокируем (чтобы не банить)
            bot.ban_chat_member(chat_id, uid)
            bot.unban_chat_member(chat_id, uid)

            if is_anonymous:
                logger.info(f"Удалён [без имени] ({uid}) — неактивен с {last_active}")
                removed_anonymous += 1
            else:
                logger.info(f"Удалён @{username} ({uid}) — неактивен с {last_active}")

            removed += 1
            del user_activity[user_id_str]

    except telebot.apihelper.ApiTelegramException as e:
        if "user is an administrator" in str(e):
            logger.warning(f"Нельзя удалить админа @{username} ({uid}): {e}")
        elif "not enough rights" in str(e):
            logger.warning(f"Нет прав для удаления @{username} ({uid}): {e}")
        else:
            logger.error(f"Ошибка Telegram API при удалении {uid}: {e}")

    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке {uid}: {e}")