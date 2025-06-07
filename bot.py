import logging
from aiogram import Bot, Dispatcher, types, executor
import os

# Load from environment variable
API_TOKEN = os.getenv("API_TOKEN")

# === CONFIGURATION ===
ADMIN_USERNAME = "@REDDOT016"
SOLANA_WALLET = "2BW8GnRa36iy5V9ihJZrssPYYfx37G16z8JSFdVfUrsg"

# CODM CP Packages
CP_PACKAGES = {
    "3000 CP": "₦40,000",
    "5000 CP": "₦58,000",
    "10000 CP": "₦75,000",
    "10800 CP": "₦80,000",
    "15000 CP": "₦120,000",
    "20000 CP": "₦140,000"
}

# === BOT SETUP ===
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Temporary user data
user_data = {}

# === START COMMAND ===
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    for cp, price in CP_PACKAGES.items():
        keyboard.add(types.InlineKeyboardButton(f"{cp} ({price})", callback_data=cp))
    await message.answer("🎮 Welcome!\nSelect a CP package below:", reply_markup=keyboard)

# === PACKAGE SELECTED ===
@dp.callback_query_handler(lambda c: c.data in CP_PACKAGES)
async def handle_package_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    selected = callback_query.data
    user_data[user_id] = {"cp": selected}
    await bot.send_message(user_id, f"You selected *{selected}*\n\nNow enter your UID:", parse_mode="Markdown")
    await bot.answer_callback_query(callback_query.id)

# === UID COLLECTED ===
@dp.message_handler(lambda message: message.chat.id in user_data and "uid" not in user_data[message.chat.id])
async def get_uid(message: types.Message):
    user_id = message.chat.id
    user_data[user_id]["uid"] = message.text

    # Step 1: Instruction
    await message.answer("💸 Send a screenshot of your payment to the wallet below:\n\nSolana Address:")

    # Step 2: Address sent separately (copyable)
    await message.answer(SOLANA_WALLET)

    # === ADMIN ALERT ===
    cp = user_data[user_id]["cp"]
    uid = user_data[user_id]["uid"]
    username = message.from_user.username or "No username"
    admin_message = (
        f"📥 New CP Order!\n\n"
        f"👤 User: @{username}\n"
        f"📦 Package: {cp}\n"
        f"🆔 UID: {uid}\n"
        f"💰 Price: {CP_PACKAGES[cp]}"
    )
    await bot.send_message(chat_id=ADMIN_USERNAME, text=admin_message)

# === START BOT ===
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
