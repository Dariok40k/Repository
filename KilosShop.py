from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Товары (хранятся в памяти)
PRODUCTS = {
    1: {
        "name": "Футболка с логотипом",
        "description": "Хлопковая футболка, унисекс",
        "price": 990,
        "photo": "https://example.com/tshirt.jpg"  # замените на реальную ссылку
    },
    2: {
        "name": "Кружка «Лучший»",
        "description": "Керамическая, объём 300 мл",
        "price": 450,
        "photo": "https://example.com/mug.jpg"
    },
    3: {
        "name": "Блокнот А5",
        "description": "100 страниц, твёрдая обложка",
        "price": 290,
        "photo": "https://example.com/notebook.jpg"
    }
}

# Заказы (хранятся в памяти)
ORDERS = []  # список заказов: {"user_id": ..., "product_id": ..., "quantity": 1}

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
    
    await query.message.edit_text("Выберите товар:")
    
    for product_id, data in PRODUCTS.items():
        caption = (
            f"<b>{data['name']}</b>\n"
            f"{data['description']}\n"
            f"Цена: <b>{data['price']} руб.</b>"
        )
        await query.message.reply_photo(
            photo=data["photo"],
            caption=caption,
            parse_mode="HTML",
            reply_markup=product_keyboard(product_id)
        )

async def buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[1])
    
    product = PRODUCTS.get(product_id)
    if not product:
        await query.edit_message_text("Товар не найден.")
        return
    
    caption = (
        f"Вы выбрали:\n<b>{product['name']}</b>\n"
        f"{product['description']}\n"
        f"Цена: <b>{product['price']} руб.</b>"
    )
    await query.edit_message_caption(
        caption=caption,
        parse_mode="HTML",
        reply_markup=confirm_keyboard(product_id)
    )

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[1])
    user_id = query.from_user.id
    
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

# Запуск бота
def main():
    # Замените на ваш токен от @BotFather
    TOKEN = "8280534725:AAEgTg7skIOegUt5wSSQIrG_ItKPiUgXwGE"
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_catalog, pattern="^catalog$"))
    application.add_handler(CallbackQueryHandler(buy_product, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(confirm_order, pattern="^confirm_"))
    application.add_handler(CallbackQueryHandler(show_orders, pattern="^my_orders$"))
    application.add_handler(CallbackQueryHandler(show_help, pattern="^help$"))
    
    application.run_polling()

if __name__ == "__main__":
    main()