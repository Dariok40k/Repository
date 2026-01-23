from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.ext import filters

import logging

ADMIN_ID = 247875327

# Состояние диалога (кто и что заполняет)
USER_STATE = {}  # {user_id: "waiting_name", "waiting_phone", ...}


# Временные данные заказов (до подтверждения)
TEMP_ORDERS = {}  # {user_id: {"product_id": ..., "name": None, "phone": None, "address": None}}

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Товары (хранятся в памяти)
PRODUCTS = {
    1: {
        "name": "Футболка с логотипом",
        "description": "Хлопковая футболка, унисекс",
        "price": 990
    },
    2: {
        "name": "Кружка «Лучший»",
        "description": "Керамическая, объём 300 мл",
        "price": 450
    },
    3: {
        "name": "Блокнот А5",
        "description": "100 страниц, твёрдая обложка",
        "price": 290
    }
}

# Заказы (хранятся в памяти)
ORDERS = []  # список: {"user_id": ..., "product_id": ..., "quantity": 1}

# Клавиатуры
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Каталог", callback_data="catalog")],
        [InlineKeyboardButton("Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def product_keyboard(product_id):
    keyboard = [
        [InlineKeyboardButton("Купить", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton("Назад", callback_data="catalog")]
    ]
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(product_id):
    keyboard = [
        [InlineKeyboardButton("Подтвердить", callback_data=f"confirm_{product_id}")],
        [InlineKeyboardButton("Отменить", callback_data="catalog")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработчики
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте! Добро пожаловать в наш магазин.",
        reply_markup=main_menu()
    )

async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        await query.delete_message()  # Убираем старое меню
        
        if not PRODUCTS:
            await query.message.reply_text("Товары отсутствуют.")
            return
        
        # Формируем текст каталога
        catalog_text = "<b>Каталог товаров:</b>\n\n"
        for product_id, data in PRODUCTS.items():
            catalog_text += (
                f"<b>{data['name']}</b>\n"
                f"{data['description']}\n"
                f"Цена: <b>{data['price']} руб.</b>\n"
            )
            catalog_text += "\n"  # Разделитель между товарами
        
        # Отправляем каталог и кнопки для каждого товара
        for product_id, data in PRODUCTS.items():
            await query.message.reply_html(
                f"<b>{data['name']}</b>\n{data['description']}\nЦена: <b>{data['price']} руб.</b>",
                reply_markup=product_keyboard(product_id)
            )
            
    except Exception as e:
        logger.error(f"Ошибка в show_catalog: {e}")
        await query.message.reply_text(f"Ошибка: {e}")

async def buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[1])
    
    user_id = query.from_user.id

    # Проверяем, есть ли товар
    product = PRODUCTS.get(product_id)
    if not product:
        await query.edit_message_text("Товар не найден.")
        return

    # Сохраняем выбранный товар
    TEMP_ORDERS[user_id] = {
        "product_id": product_id,
        "name": None,        # имя пользователя
        "phone": None,      # телефон
        "address": None       # адрес
    }
    USER_STATE[user_id] = "waiting_name"


    # Спрашиваем имя
    await query.edit_message_text(
        f"Вы выбрали: <b>{product['name']}</b>\n"
        "Для оформления заказа укажите ваше имя:",
        parse_mode="HTML"
    )

async def handle_user_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()


    # Если пользователь не в процессе заполнения
    if user_id not in USER_STATE:
        return

    state = USER_STATE[user_id]

    if state == "waiting_name":
        TEMP_ORDERS[user_id]["name"] = text
        USER_STATE[user_id] = "waiting_phone"
        await update.message.reply_text("Укажите ваш телефон для связи:")


    elif state == "waiting_phone":
        # Проверяем формат телефона (упрощённо)
        if not (text.isdigit() and len(text) >= 10):
            await update.message.reply_text("Пожалуйста, введите корректный номер телефона (10–11 цифр):")
            return
        TEMP_ORDERS[user_id]["phone"] = text
        USER_STATE[user_id] = "waiting_address"
        await update.message.reply_text("Укажите адрес доставки:")

    elif state == "waiting_address":
        TEMP_ORDERS[user_id]["address"] = text


        # Формируем заказ
        order = TEMP_ORDERS[user_id]
        product = PRODUCTS[order["product_id"]]


        # Сохраняем в ORDERS
        ORDERS.append({
            "user_id": user_id,
            "product_id": order["product_id"],
            "quantity": 1,
            "name": order["name"],
            "phone": order["phone"],
            "address": order["address"],
            "status": "новый"
        })

        # Очищаем временные данные
        del USER_STATE[user_id]
        del TEMP_ORDERS[user_id]


        # Отчёт администратору
        await context.bot.send_message(
            ADMIN_ID,
            f"<b>Новый заказ!</b>\n"
            f"Пользователь: {user_id}\n"
            f"Товар: {product['name']}\n"
            f"Имя: {order['name']}\n"
            f"Телефон: {order['phone']}\n"
            f"Адрес: {order['address']}",
            parse_mode="HTML"
        )

        # Подтверждение пользователю
        await update.message.reply_html(
            f"✅ Заказ оформлен!\n\n"
            f"<b>Товар:</b> {product['name']}\n"
            f"<b>Имя:</b> {order['name']}\n"
            f"<b>Телефон:</b> {order['phone']}\n"
            f"<b>Адрес:</b> {order['address']}\n\n"
            "Мы свяжемся с вами для уточнения деталей."
        )

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[1])

    await buy_product(update, context)

    ORDERS.append({
        "user_id": user_id,
        "product_id": product_id,
        "quantity": 1
    })
    
    await query.edit_message_text("✅ Заказ оформлен! Мы свяжемся с вами для уточнения деталей.")

async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_orders = [order for order in ORDERS if order["user_id"] == user_id]
    
    if not user_orders:
        await query.edit_message_text("У вас нет заказов.")
        return
    
    message = "Ваши заказы:\n"
    for order in user_orders:
        product = PRODUCTS[order["product_id"]]
        message += f"- {product['name']} (×{order['quantity']})\n"
    
    await query.edit_message_text(message)

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Помощь:\n"
        "1. «Каталог» — посмотреть товары.\n"
        "2. «Мои заказы» — увидеть свои заказы.\n"
        "3. Нажмите «Купить», чтобы оформить заказ."
    )

async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Проверяем, что это администратор
    if user_id != ADMIN_ID:
        await update.message.reply_text("Доступ запрещён.")
        return

    if not ORDERS:
        await update.message.reply_text("Заказаов пока нет.")
        return

    # Формируем отчёт
    report = "<b>Список всех заказов:</b>\n\n"
    for order in ORDERS:
        product = PRODUCTS[order["product_id"]]
        report += (
            f"🔹 Заказ №{len(report.splitlines())}\n"
            f"   Пользователь: {order['user_id']}\n"
            f"   Товар: {product['name']}\n"
            f"   Количество: ×{order['quantity']}\n"
            f"   Цена: {product['price']} руб.\n\n"
        )

    await update.message.reply_html(report)


# Запуск бота
def main():
    # Замените на ваш токен от @BotFather
    TOKEN = "8280534725:AAEgTg7skIOegUt5wSSQIrG_ItKPiUgXwGE"
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_orders))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_response))
    application.add_handler(CallbackQueryHandler(show_catalog, pattern="^catalog$"))
    application.add_handler(CallbackQueryHandler(buy_product, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(confirm_order, pattern="^confirm_"))
    application.add_handler(CallbackQueryHandler(show_orders, pattern="^my_orders$"))
    application.add_handler(CallbackQueryHandler(show_help, pattern="^help$"))
    
    application.run_polling()

if __name__ == "__main__":
    main()