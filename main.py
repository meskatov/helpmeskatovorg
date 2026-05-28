import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Хранилище платежей (в реальном проекте используйте БД)
user_sessions = {}
star_payments = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⭐ Поддержать звездами", callback_data="star_pay")],
        [InlineKeyboardButton("💰 Другое", callback_data="other")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌟 *Поддержка Мескатова* 🌟\n\n"
        "Выбери способ поддержки:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "star_pay":
        await query.edit_message_text(
            "💫 *Оплата звездами*\n\n"
            "Введите сумму (целое число):\n"
            "Пример: `2`\n\n"
            "Минимум: 1 звезда",
            parse_mode="Markdown"
        )
        user_sessions[query.from_user.id] = "awaiting_star_amount"
    
    elif query.data == "other":
        await query.edit_message_text("Другие способы: свяжитесь с @MeskatovSupport")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_sessions.get(user_id) == "awaiting_star_amount":
        try:
            amount = int(update.message.text.strip())
            if amount < 1:
                await update.message.reply_text("❌ Сумма должна быть от 1 звезды")
                return
            
            # Создаем инвойс для оплаты звездами
            await context.bot.send_invoice(
                chat_id=user_id,
                title="⭐ Поддержка Мескатова",
                description=f"Пожертвование {amount} звезд",
                payload=f"donation_{amount}_{user_id}",
                currency="XTR",  # XTR = Telegram Stars
                prices=[{"label": f"{amount} звезд", "amount": amount}],
                start_parameter="support_meskatov"
            )
            user_sessions[user_id] = f"paid_{amount}"
            
        except ValueError:
            await update.message.reply_text("❌ Введи число, например: 5")

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    amount = payment.total_amount
    user_id = update.message.from_user.id
    
    # Логируем платеж
    print(f"✅ Пользователь {user_id} задонатил {amount} звезд")
    
    await update.message.reply_text(
        f"✨ *Спасибо за поддержку!* ✨\n\n"
        f"Получено: ⭐ {amount} звезд\n"
        f"Мескатов благодарит тебя!\n\n"
        f"*Всего собрано:* {star_payments.get('total', 0) + amount} звезд",
        parse_mode="Markdown"
    )
    star_payments['total'] = star_payments.get('total', 0) + amount

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    
    print("🤖 Бот 'Поддержка Мескатова' запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
