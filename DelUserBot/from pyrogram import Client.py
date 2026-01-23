import asyncio
from pyrogram import Client
from datetime import datetime, timezone, timedelta
import json
import os
from pyrogram.errors import FloodWait, PeerIdInvalid, UsernameNotOccupied

# Настройки
api_id = 29664255
api_hash = "89a43fab6a5944a1da7e646318a7b3e9"
group_id = -1002361725921
session_name = "my_user_session"
output_path = "activity.json"

# ✏️ ЛИМИТ на количество сканируемых сообщений
MAX_MESSAGES = 50000  # Задайте нужное число


app = Client(session_name, api_id=api_id, api_hash=api_hash)


user_activity = {}
default_date = datetime(2000, 1, 1, tzinfo=timezone.utc).isoformat()  # 01.01.2000 в ISO

async def main():
    async with app:
        print("✅ Сессия запущена. Получаем участников...")
        count_members = 0
        try:
            async for member in app.get_chat_members(group_id):
                user = member.user
                if user.is_bot:
                    continue
                uid = str(user.id)
                username = user.username or user.first_name or "Unknown"
                user_activity[uid] = {
                    "username": username,
                    "last_active": default_date
                }
                count_members += 1
                if count_members % 100 == 0:
                    print(f"🧍‍♂️ Обработано участников: {count_members}")
        except (FloodWait, PeerIdInvalid, UsernameNotOccupied) as e:
            print(f"❌ Ошибка при получении участников: {e}")


        print(f"🧍‍♂️ Всего участников: {count_members}")

        print("⌛ Сканируем историю сообщений и обновляем даты активности...")

        count_messages = 0
        try:
            async for message in app.get_chat_history(group_id):
                count_messages += 1

                # Проверка на превышение лимита
                if count_messages > MAX_MESSAGES:
                    print(f"⚠️ Достигнут лимит в {MAX_MESSAGES} сообщений. Остановка сканирования.")
                    break

                if message.from_user:
                    uid = str(message.from_user.id)
                    last_active = message.date.astimezone(timezone.utc).isoformat()
                    if uid in user_activity:
                        if last_active > user_activity[uid]["last_active"]:
                            user_activity[uid]["last_active"] = last_active

                if count_messages % 500 == 0:
                    print(f"📨 Обработано сообщений: {count_messages}")
        except FloodWait as e:
            print(f"⏳ Нужно подождать {e.x} секунд из‑за FloodWait...")
            await asyncio.sleep(e.x)
        except PeerIdInvalid:
            print("❌ Неверный Peer ID, пропускаем сообщение...")
        except Exception as e:
            print(f"❌ Другая ошибка при чтении истории: {e}")

        print(f"✅ Обработка истории завершена. Всего обработано сообщений: {count_messages}")

        # ✏️ РАСЧЁТ: сколько пользователей были неактивны >30 дней
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        inactive_count = 0

        for user_data in user_activity.values():
            last_active_str = user_data["last_active"]
            # Преобразуем ISO‑строку в datetime
            try:
                last_active = datetime.fromisoformat(last_active_str)
                if last_active < thirty_days_ago:
                    inactive_count += 1
            except ValueError:
                # Если формат даты нераспознан, считаем пользователя неактивным
                inactive_count += 1

        print(f"📊 Пользователей с активностью более 30 дней назад: {inactive_count}")

        # Сохранение результатов
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(user_activity, f, ensure_ascii=False, indent=2)

        print(f"📁 Файл сохранён: {os.path.abspath(output_path)}")

# Запуск
if __name__ == "__main__":
    asyncio.run(main())
