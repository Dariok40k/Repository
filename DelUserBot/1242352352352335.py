from pyrogram import Client

api_id = 29664255
api_hash = "89a43fab6a5944a1da7e646318a7b3e9"

with Client("test_scan", api_id, api_hash) as app:
    print("=== Доступные чаты ===")
    for dialog in app.get_dialogs():
        chat = dialog.chat
        print(chat.id, chat.type, chat.title)