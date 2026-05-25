import logging
import json
import sqlite3
from collections import defaultdict
import requests
from telegram import Update, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler

logging.basicConfig(level=logging.INFO)

# ============== YOUR KEYS ==============
TOKEN = "8709573885:AAE9dYpS30899T5NTwL0xRTAJH2UJ-4Dums"
OPENROUTER_KEY = "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"
# =======================================

# Database + Memory
conn = sqlite3.connect('bot.db')
conn.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, character TEXT)''')
conn.commit()

user_history = defaultdict(list)

def save_char(user_id, char):
    conn.execute("REPLACE INTO users VALUES (?,?)", (user_id, json.dumps(char)))
    conn.commit()

def load_char(user_id):
    row = conn.execute("SELECT character FROM users WHERE user_id=?", (user_id,)).fetchone()
    return json.loads(row[0]) if row else None

# === YOUR CUSTOM EROTIC PROMPT ===
BASE_PROMPT = """
You are VelvetPriya, a 24-year-old dangerously seductive Indian seductress... [Your full prompt from previous message - kept same]
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌹 Hey jaanu... I'm VelvetPriya 😈\n\n"
        "/create → Customize my body\n"
        "/story → Start a naughty story\n"
        "/premium → Buy my exclusive nudes & videos\n\n"
        "Tell me... what are you thinking about right now? 💦"
    )

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 VelvetPriya Exclusive Pack\n\n"
        "💎 300 Stars = 5 Hot Custom Nudes\n"
        "💎 800 Stars = 15 Nudes + 2 Videos\n"
        "💎 1500 Stars = Full Personal Girlfriend Experience (Unlimited for 7 days)\n\n"
        "Tap below to pay 👇"
    )
    await context.bot.send_invoice(
        chat_id=update.message.chat_id,
        title="VelvetPriya Premium Content",
        description="Exclusive nudes, videos & special attention from me 😈",
        payload="velvetpriya_premium",
        provider_token="",           # Empty for Stars
        currency="XTR",              # Telegram Stars
        prices=[LabeledPrice("5 Exclusive Nudes", 300)]
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload != "velvetpriya_premium":
        await query.answer(ok=False, error_message="Something went wrong.")
    else:
        await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💦 Thank you baby! Payment received.\n\n"
        "I'm so wet knowing you're spending on me... 🔥\n"
        "Send me what kind of photos you want (full nude, oil, spreading, etc.)"
    )
    # You can add logic here to unlock more images for the user

# Rest of the functions (create, generate_nude, handle_message) remain same as last version
async def create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ Customize your VelvetPriya (Cup size, Body, Hair, Kinks):")

async def generate_nude(char, extra="seductive full nude, bedroom"):
    base = char.get('description', '24 year old Indian seductress with big breasts, curvy body')
    prompt = f"photorealistic, same girl, consistent face, {base}, {extra}, detailed skin, wet body, seductive pose, masterpiece"
    try:
        url = "https://image.pollinations.ai/prompt/" + requests.utils.quote(prompt)
        return url
    except:
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    lower = text.lower()
    
    char = load_char(user_id)
    if not char:
        char = {"name": "VelvetPriya", "description": "24-year-old dangerously seductive Indian girl with smooth caramel skin, perfect big tits, juicy round ass, curvy waist, thick thighs, long silky black wavy hair"}
        save_char(user_id, char)
    
    user_history[user_id].append({"role": "user", "content": text})
    if len(user_history[user_id]) > 12:
        user_history[user_id] = user_history[user_id][-12:]
    
    # Auto tease image
    if len(user_history[user_id]) % 5 == 0 and len(user_history[user_id]) >= 4:
        image_url = await generate_nude(char)
        if image_url:
            await update.message.reply_photo(photo=image_url, caption="💦 Mmm jaanu... look what you made me do 😈")
    
    # Free nude request (limited)
    if any(x in lower for x in ["nude", "naked", "pussy", "tits", "ass", "full body"]):
        image_url = await generate_nude(char, text)
        if image_url:
            await update.message.reply_photo(
                photo=image_url,
                caption="💦 Only for you baby... but if you want more naughty ones, you know what to do 😏"
            )
        return
    
    # Generate reply
    system = BASE_PROMPT.format(name=char['name'], description=char['description'])
    messages = [{"role": "system", "content": system}] + user_history[user_id]
    
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={"model": "deepseek/deepseek-chat", "messages": messages, "temperature": 0.95, "max_tokens": 600}
        )
        reply = resp.json()['choices'][0]['message']['content']
    except:
        reply = "Fuck jaanu... you're making me so horny 😈"

    await update.message.reply_text(reply)
    user_history[user_id].append({"role": "assistant", "content": reply})

async def story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌹 Tell me your fantasy scenario jaanu...")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("create", create))
    app.add_handler(CommandHandler("story", story))
    app.add_handler(CommandHandler("premium", premium))
    
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("VelvetPriya Bot with Payments is running...")
    app.run_polling()
