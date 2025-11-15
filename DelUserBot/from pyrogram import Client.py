import asyncio
from pyrogram import Client
from datetime import datetime, timezone
import json
import os
from pyrogram.errors import FloodWait, PeerIdInvalid, UsernameNotOccupied

# Настройки
api_id = 29664255
api_hash = "89a43fab6a5944a1da7e646318a7b3e9"
group_id = -1002361725921
session_name = "my_user_session"
output_path = "activity.json"

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
                if message.from_user:
                    uid = str(message.from_user.id)
                    last_active = message.date.astimezone(timezone.utc).isoformat()
                    if uid in user_activity:
                        if last_active > user_activity[uid]["last_active"]:
                            user_activity[uid]["last_active"] = last_active
                
                if count_messages % 500 == 0:
                    print(f"📨 Обработано сообщений: {count_messages}")
        except FloodWait as e:
            print(f"⏳ Нужно подождать {e.x} секунд из-за FloodWait...")
            await asyncio.sleep(e.x)
        except PeerIdInvalid:
            print("❌ Неверный Peer ID, пропускаем сообщение...")
        except Exception as e:
            print(f"❌ Другая ошибка при чтении истории: {e}")

        print(f"✅ Обработка истории завершена. Всего сообщений: {count_messages}")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(user_activity, f, ensure_ascii=False, indent=2)

        print(f"📁 Файл сохранён: {os.path.abspath(output_path)}")

# Запуск
if __name__ == "__main__":
    asyncio.run(main())
