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



bot.polling()
    
