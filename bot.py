import telebot
import requests
import json
import time
import os
import random
import string

# Use environment variables for security
BOT_TOKEN = "8441050494:AAHYReJVCmIW0v7ytn3ye2xhKHpm6LbV9mA"
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing! Set it as an environment variable.")

bot = telebot.TeleBot(BOT_TOKEN)

# API URL Template
API_URL = "https://vhbj.vercel.app/token?uid={uid}&password={password}"

# Required Telegram Channel
CHANNEL_USERNAME = "@shsvacscscsc"

# Function to check if user has joined the channel
def is_subscribed(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except Exception:
        return False  # Handles cases where the bot can't get the user info

# Function to generate a random file name
def generate_random_filename():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + ".json"

# Function to process JSON file and generate tokens
def process_json(file_path, chat_id):
    with open(file_path, "r") as file:
        try:
            json_data = json.load(file)
        except json.JSONDecodeError:
            bot.send_message(chat_id, "⚠️ Invalid JSON format! Please check your file.")
            return

    if not isinstance(json_data, list) or len(json_data) == 0:
        bot.send_message(chat_id, "⚠️ JSON must be a list of objects and contain at least 1 ID!")
        return

    tokens = []
    total = len(json_data)

    # Send initial processing message
    progress_message = bot.send_message(chat_id, f"🔄 *Processing {total} IDs...*", parse_mode="Markdown")

    for index, entry in enumerate(json_data):
        if not all(k in entry for k in ["uid", "password"]):
            continue

        uid, password = entry["uid"], entry["password"]

        try:
            response = requests.get(API_URL.format(uid=uid, password=password), timeout=10)
            response.raise_for_status()
            response_data = response.json()

            if isinstance(response_data, dict) and "token" in response_data:
                tokens.append({"token": response_data["token"]})
        except requests.exceptions.RequestException:
            bot.send_message(chat_id, f"⚠️ Failed to fetch data for UID {uid}. Skipping...")
            continue

        # Update real-time progress (edit message instead of sending new)
        percent = int((index + 1) / total * 100)
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=progress_message.message_id,
                                  text=f"⏳ *Generating JWT token... {percent}% ✅*", parse_mode="Markdown")
        except Exception:
            pass  # Prevents crashing if message editing fails

        time.sleep(0.2)  # Reduced delay for faster execution

    if tokens:
        os.makedirs("tokens", exist_ok=True)  # Ensure folder exists
        output_filename = generate_random_filename()
        output_path = os.path.join("tokens", output_filename)

        with open(output_path, "w") as output_file:
            json.dump(tokens, output_file, indent=4)

        with open(output_path, "rb") as file:
            bot.send_document(chat_id, file, caption="✅ *Here is your generated token file!*", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "⚠️ No valid tokens found!")

# Start Command
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.chat.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "❌ You must join our channel to use this bot: [Join Now](https://t.me/shsvacscscsc)", parse_mode="Markdown")
        return

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(telebot.types.KeyboardButton("📤 Upload JSON"), telebot.types.KeyboardButton("ℹ️ Help"))

    bot.send_message(
        user_id,
        "👋 *Welcome to the Token Generator Bot!*\n\n"
        "📂 Send me a `.json` file, and I'll extract the tokens for you!\n"
        "🔄 Real-time processing updates included!",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# Handle JSON File Upload
@bot.message_handler(content_types=["document"])
def handle_docs(message):
    user_id = message.chat.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "❌ You must join our channel to use this bot: [Join Now](https://t.me/teamxcutehacker)", parse_mode="Markdown")
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    os.makedirs("uploads", exist_ok=True)  # Ensure folder exists
    filename = generate_random_filename()
    file_path = os.path.join("uploads", filename)

    with open(file_path, "wb") as new_file:
        new_file.write(downloaded_file)

    process_json(file_path, user_id)

# Help Command
@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ *How to Use the Bot:*\n"
        "1️⃣ Send me a `.json` file containing your `uid` and `password`.\n"
        "2️⃣ The bot will generate JWT tokens for you.\n"
        "3️⃣ You will receive a `.json` file with the extracted tokens.\n"
        "✅ *Make sure you have joined our channel:* [@teamxcutehacker](https://t.me/shsvacscscsc)",
        parse_mode="Markdown"
    )

# Run Bot
bot.polling()
