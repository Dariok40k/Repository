from   import TelegramClient
from datetime import datetime, timedelta

api_id = 29664255
api_hash = '89a43fab6a5944a1da7e646318a7b3e9'
group = 'ДАУНФЛАЙ ФЛУДИЛКА'
inactivity_days = 99

client = TelegramClient('session', api_id, api_hash)

async def cleanup():
    async with client:
        threshold = datetime.now() - timedelta(inactivity_days)
        async for user in client.iter_participants(group):
            if user.status and hasattr(user.status, 'was_online'):
                if user.status.was_online < threshold:
                    try:
                        await client.kick_participant(group, user.id)
                        print(f'Removed {user.id}')
                    except Exception as e:
                        print(f'Failed to remove {user.id}: {e}')

client.loop.run_until_complete(cleanup())