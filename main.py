import os
import telebot
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Bot ishlayapti ✅")


@app.route("/")
def home():
    return "Bot is running"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(
        url=f"https://mathsolverbot-2.onrender.com/{BOT_TOKEN}"
    )
    app.run(host="0.0.0.0", port=10000)
