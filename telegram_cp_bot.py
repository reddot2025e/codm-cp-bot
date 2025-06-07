from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import json

# Load config
with open("cp_bot_config.json", "r") as f:
    config = json.load(f)

API_TOKEN = config['token']
ADMIN_USERNAME = config['admin_username']

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class OrderForm(StatesGroup):
    waiting_for_uid = State()
    waiting_for_payment = State()

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    for pkg in config['cp_packages']:
        text = f"{pkg['amount']} – {pkg['usd_price']} ({pkg['naira_price']})"
        kb.add(InlineKeyboardButton(text=text, callback_data=pkg['amount']))
    await message.answer("Welcome! Select a CP package:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.endswith('CP'))
async def package_selected(callback_query: types.CallbackQuery):
    pkg = callback_query.data
    await bot.send_message(callback_query.from_user.id, f"You selected {pkg}. Please enter your UID:")
    state = dp.current_state(user=callback_query.from_user.id)
    await state.set_state(OrderForm.waiting_for_uid.state)
    await state.update_data(package=pkg)

@dp.message_handler(state=OrderForm.waiting_for_uid)
async def process_uid(message: types.Message, state: FSMContext):
    await state.update_data(uid=message.text)
    await message.answer("Send a screenshot of your payment to this wallet:\n\n" +
                         f"Solana Address: `{config['payment_method']['address']}`",
                         parse_mode='Markdown')
    await OrderForm.next()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=OrderForm.waiting_for_payment)
async def process_payment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    package = data['package']
    uid = data['uid']
    admin_msg = (f"📥 *New Order Received!*\n"
                 f"👤 User: @{message.from_user.username or message.from_user.id}\n"
                 f"🎮 Package: {package}\n🆔 UID: {uid}")
    await bot.send_photo(chat_id=ADMIN_USERNAME, photo=message.photo[-1].file_id, caption=admin_msg, parse_mode='Markdown')
    await message.answer("✅ Your order has been submitted! You'll be contacted shortly.")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
