from telethon import TelegramClient
from datetime import datetime, timedelta

api_id = 29664255
api_hash = '89a43fab6a5944a1da7e646318a7b3e9'
group = 'ДАУНФЛАЙ ФЛУДИЛКА' 
inactivity_days = 99

client = TelegramClient('session', api_id, api_hash)

async def cleanup():
    async with client:
        threshold = datetime.now() - timedelta(days=inactivity_days)
        async for user in client.iter_participants(group):
            if user.bot:
                continue

            if user.status and hasattr(user.status, 'was_online'):
                if user.status.was_online < threshold:
                    try:
                   
                        await client.kick_participant(group, user.id)
                        await client.edit_permissions(group, user.id, view_messages=True)
                        print(f'Removed inactive user: {user.id}')
                    except Exception as e:
                        print(f'Failed to remove {user.id}: {e}')
            else:
              
                print(f'Skipped user {user.id} (hidden last seen or offline)')

client.loop.run_until_complete(cleanup())