"""
🎮 TELEGRAM MINI O'YINLAR BOTI
================================
Kerakli kutubxonalar:
  pip install aiogram==3.x

Ishga tushirish:
  python game_bot.py

@BotFather dan token olish:
  1. Telegramda @BotFather ga yozing
  2. /newbot buyrug'ini yuboring
  3. Bot nomini kiriting
  4. Token oling va BOT_TOKEN ga qo'ying
"""

import asyncio
import random
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ===== SOZLAMALAR =====
BOT_TOKEN = "SENING_BOT_TOKEN_NI_BU_YERGA_QOY"  # @BotFather dan olingan token
ADMIN_ID = 123456789  # Sening Telegram ID'ing (@userinfobot dan olish mumkin)

# ===== MA'LUMOTLAR BAZASI (fayl asosida) =====
DB_FILE = "users.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def get_user(user_id: int):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {
            "coins": 100,       # Boshlang'ich coin
            "wins": 0,
            "games_played": 0,
            "referrals": 0,
            "name": ""
        }
        save_db(db)
    return db[uid]

def update_user(user_id: int, data: dict):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"coins": 100, "wins": 0, "games_played": 0, "referrals": 0, "name": ""}
    db[uid].update(data)
    save_db(db)

def add_coins(user_id: int, amount: int):
    user = get_user(user_id)
    new_coins = user["coins"] + amount
    update_user(user_id, {"coins": new_coins})
    return new_coins

# ===== STATES =====
class GuessGame(StatesGroup):
    playing = State()

class CardGame(StatesGroup):
    playing = State()

# ===== BOT VA DISPATCHER =====
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== KLAVIATURA =====
def main_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎮 O'yinlar")
    kb.button(text="💰 Balans")
    kb.button(text="🏆 Reyting")
    kb.button(text="👥 Do'stlarni taklif qil")
    kb.button(text="ℹ️ Yordam")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

def games_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🃏 Karta o'yini", callback_data="game_card")
    builder.button(text="🔢 Sonni top", callback_data="game_guess")
    builder.button(text="🎲 Zar tashlash", callback_data="game_dice")
    builder.button(text="🪙 Tanga", callback_data="game_coin")
    builder.button(text="🧮 Matematika", callback_data="game_math")
    builder.button(text="⬅️ Orqaga", callback_data="back_main")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()

# ===== /START =====
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "O'yinchi"
    
    # Referral tekshirish
    args = message.text.split()
    if len(args) > 1:
        ref_id = args[1]
        if ref_id.isdigit() and int(ref_id) != user_id:
            ref_user = get_user(int(ref_id))
            add_coins(int(ref_id), 100)
            ref_data = get_user(int(ref_id))
            update_user(int(ref_id), {"referrals": ref_data["referrals"] + 1})
            try:
                await bot.send_message(
                    int(ref_id),
                    f"🎉 Do'stingiz {name} botga qo'shildi!\n+100 coin oldiniz! 🪙"
                )
            except:
                pass
    
    user = get_user(user_id)
    update_user(user_id, {"name": name})
    
    text = f"""
🎮 *Game Zone Botiga Xush Kelibsiz!*

Salom, *{name}*! 👋

Sizda hozir: 🪙 *{user['coins']} coin*

📋 *Nima qila olasiz:*
• 5 xil mini o'yin o'ynash
• Coin yig'ish
• Do'stlarni taklif qilib coin olish
• Reyting jadvalida yuqoriga chiqish

Boshlaylik! 👇
"""
    await message.answer(text, reply_markup=main_keyboard(), parse_mode="Markdown")

# ===== ASOSIY MENYULAR =====
@dp.message(F.text == "🎮 O'yinlar")
async def show_games(message: types.Message):
    await message.answer(
        "🎮 *Qaysi o'yinni tanlaysiz?*\n\nHar o'yin coin yutish imkonini beradi!",
        reply_markup=games_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "💰 Balans")
async def show_balance(message: types.Message):
    user = get_user(message.from_user.id)
    text = f"""
💰 *Sizning hisobingiz*

🪙 Coin: *{user['coins']}*
🏆 G'alabalar: *{user['wins']}*
🎮 O'yinlar: *{user['games_played']}*
👥 Taklif qilinganlar: *{user['referrals']}*
"""
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "👥 Do'stlarni taklif qil")
async def referral(message: types.Message):
    user_id = message.from_user.id
    link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
    text = f"""
👥 *Referral tizimi*

Do'stingizni taklif qiling:
• Siz: *+100 coin* olasiz
• Do'stingiz: *+100 coin* oladi

🔗 *Sizning havolangiz:*
`{link}`

Yuqoridagi havolani nusxalab do'stlaringizga yuboring!
"""
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🏆 Reyting")
async def show_rating(message: types.Message):
    db = load_db()
    sorted_users = sorted(db.items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:10]
    
    text = "🏆 *TOP 10 O'yinchilar*\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, (uid, data) in enumerate(sorted_users):
        name = data.get("name", "Noma'lum")
        coins = data.get("coins", 0)
        text += f"{medals[i]} {name}: 🪙 {coins}\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "ℹ️ Yordam")
async def help_cmd(message: types.Message):
    text = """
ℹ️ *Yordam*

🎮 *O'yinlar:*
• 🃏 Karta — katta karta yutadi (+20 coin)
• 🔢 Sonni top — 1-100 ni top (+10-30 coin)
• 🎲 Zar — katta son yutadi (+15 coin)
• 🪙 Tanga — toq/juft (+10 coin)
• 🧮 Matematika — hisob (+15 coin)

💡 *Coin qanday yig'iladi:*
• O'yin g'alabasi
• Do'st taklif qilish (+100)
• Kunlik bonus (+50)

📩 *Muammo bo'lsa:* @admin ga yozing
"""
    await message.answer(text, parse_mode="Markdown")

# ===== O'YINLAR =====

# --- KARTA O'YINI ---
@dp.callback_query(F.data == "game_card")
async def card_game(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id)
    
    suits = ["♠️", "♥️", "♦️", "♣️"]
    values = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
    ranks = {v: i for i, v in enumerate(values)}
    
    player_suit = random.choice(suits)
    player_val = random.choice(values)
    cpu_suit = random.choice(suits)
    cpu_val = random.choice(values)
    
    user_data = get_user(callback.from_user.id)
    games = user_data["games_played"] + 1
    update_user(callback.from_user.id, {"games_played": games})
    
    if ranks[player_val] > ranks[cpu_val]:
        result = "🎉 *Sen yutding!* +20 coin"
        new_coins = add_coins(callback.from_user.id, 20)
        wins = user_data["wins"] + 1
        update_user(callback.from_user.id, {"wins": wins})
        emoji = "🏆"
    elif ranks[player_val] < ranks[cpu_val]:
        result = "😔 *Bot yutdi...*"
        new_coins = user_data["coins"]
        emoji = "💔"
    else:
        result = "🤝 *Durrang!* +5 coin"
        new_coins = add_coins(callback.from_user.id, 5)
        emoji = "🤝"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🃏 Yana o'yna", callback_data="game_card")
    builder.button(text="⬅️ Orqaga", callback_data="back_games")
    
    text = f"""
🃏 *Karta O'yini* {emoji}

👤 Sen: *{player_val}{player_suit}*
💻 Bot: *{cpu_val}{cpu_suit}*

{result}
🪙 Coin: *{new_coins}*
"""
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# --- SONNI TOP O'YINI ---
@dp.callback_query(F.data == "game_guess")
async def guess_game_start(callback: types.CallbackQuery, state: FSMContext):
    secret = random.randint(1, 100)
    await state.set_state(GuessGame.playing)
    await state.update_data(secret=secret, attempts=0, max_attempts=7)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="cancel_game")
    
    await callback.message.edit_text(
        "🔢 *Sonni Top O'yini*\n\n1 dan 100 gacha son o'yladim...\nSon yuboring! (7 ta urinish)\n\n🪙 To'g'ri topsangiz: *+10-30 coin*",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.message(GuessGame.playing)
async def guess_check(message: types.Message, state: FSMContext):
    data = await state.get_data()
    secret = data["secret"]
    attempts = data["attempts"] + 1
    max_att = data["max_attempts"]
    
    if not message.text.isdigit():
        await message.answer("❗ Faqat son kiriting!")
        return
    
    guess = int(message.text)
    if guess < 1 or guess > 100:
        await message.answer("❗ 1 dan 100 gacha son kiriting!")
        return
    
    await state.update_data(attempts=attempts)
    left = max_att - attempts
    
    builder = InlineKeyboardBuilder()
    
    if guess == secret:
        coins_won = max(30 - attempts * 3, 5)
        new_coins = add_coins(message.from_user.id, coins_won)
        user = get_user(message.from_user.id)
        update_user(message.from_user.id, {"wins": user["wins"] + 1, "games_played": user["games_played"] + 1})
        await state.clear()
        builder.button(text="🔢 Yana o'yna", callback_data="game_guess")
        builder.button(text="🎮 O'yinlar", callback_data="back_games")
        await message.answer(
            f"🎉 *To'g'ri!* Son *{secret}* edi!\n{attempts} ta urinishda topdingiz!\n\n+{coins_won} coin! 🪙\nJami: *{new_coins} coin*",
            reply_markup=builder.as_markup(), parse_mode="Markdown"
        )
    elif attempts >= max_att:
        update_user(message.from_user.id, {"games_played": get_user(message.from_user.id)["games_played"] + 1})
        await state.clear()
        builder.button(text="🔢 Yana o'yna", callback_data="game_guess")
        builder.button(text="🎮 O'yinlar", callback_data="back_games")
        await message.answer(
            f"😔 Urinishlar tugadi!\nJavob: *{secret}* edi",
            reply_markup=builder.as_markup(), parse_mode="Markdown"
        )
    elif guess < secret:
        await message.answer(f"⬆️ Kattaroq! ({left} ta urinish qoldi)")
    else:
        await message.answer(f"⬇️ Kichikroq! ({left} ta urinish qoldi)")

# --- ZAR O'YINI ---
@dp.callback_query(F.data == "game_dice")
async def dice_game(callback: types.CallbackQuery):
    player = random.randint(1, 6)
    cpu = random.randint(1, 6)
    
    user = get_user(callback.from_user.id)
    update_user(callback.from_user.id, {"games_played": user["games_played"] + 1})
    
    dice_emoji = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣"]
    
    if player > cpu:
        result = "🎉 *Sen yutding!* +15 coin"
        new_coins = add_coins(callback.from_user.id, 15)
        update_user(callback.from_user.id, {"wins": user["wins"] + 1})
    elif player < cpu:
        result = "😔 *Bot yutdi...*"
        new_coins = user["coins"]
    else:
        result = "🤝 *Durrang!* +5 coin"
        new_coins = add_coins(callback.from_user.id, 5)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🎲 Yana o'yna", callback_data="game_dice")
    builder.button(text="⬅️ Orqaga", callback_data="back_games")
    
    await callback.message.edit_text(
        f"🎲 *Zar O'yini*\n\n👤 Sen: {dice_emoji[player-1]} ({player})\n💻 Bot: {dice_emoji[cpu-1]} ({cpu})\n\n{result}\n🪙 Coin: *{new_coins}*",
        reply_markup=builder.as_markup(), parse_mode="Markdown"
    )

# --- TANGA O'YINI ---
@dp.callback_query(F.data == "game_coin")
async def coin_game_start(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🟡 Toq", callback_data="coin_odd")
    builder.button(text="⚪ Juft", callback_data="coin_even")
    builder.button(text="⬅️ Orqaga", callback_data="back_games")
    builder.adjust(2, 1)
    
    await callback.message.edit_text(
        "🪙 *Tanga O'yini*\n\nTanga tashlayman!\nToq yoki Juft tanlang:\n\n🎯 To'g'ri topsangiz: *+10 coin*",
        reply_markup=builder.as_markup(), parse_mode="Markdown"
    )

@dp.callback_query(F.data.in_(["coin_odd", "coin_even"]))
async def coin_result(callback: types.CallbackQuery):
    result = random.choice(["odd", "even"])
    choice = "odd" if callback.data == "coin_odd" else "even"
    
    result_emoji = "🟡 Toq" if result == "odd" else "⚪ Juft"
    choice_text = "🟡 Toq" if choice == "odd" else "⚪ Juft"
    
    user = get_user(callback.from_user.id)
    update_user(callback.from_user.id, {"games_played": user["games_played"] + 1})
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🪙 Yana o'yna", callback_data="game_coin")
    builder.button(text="⬅️ Orqaga", callback_data="back_games")
    
    if choice == result:
        new_coins = add_coins(callback.from_user.id, 10)
        update_user(callback.from_user.id, {"wins": user["wins"] + 1})
        text = f"🪙 *Tanga O'yini*\n\nSen: {choice_text}\nNatija: {result_emoji}\n\n🎉 *To'g'ri!* +10 coin\n🪙 Coin: *{new_coins}*"
    else:
        text = f"🪙 *Tanga O'yini*\n\nSen: {choice_text}\nNatija: {result_emoji}\n\n😔 *Noto'g'ri!*\n🪙 Coin: *{user['coins']}*"
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# --- MATEMATIKA O'YINI ---
@dp.callback_query(F.data == "game_math")
async def math_game(callback: types.CallbackQuery):
    ops = ["+", "-", "×"]
    op = random.choice(ops)
    
    if op == "+":
        a, b = random.randint(1,50), random.randint(1,50)
        answer = a + b
    elif op == "-":
        a, b = random.randint(10,50), random.randint(1,9)
        answer = a - b
    else:
        a, b = random.randint(2,9), random.randint(2,9)
        answer = a * b
    
    # 4 ta variant
    wrong = set()
    while len(wrong) < 3:
        w = answer + random.randint(-10, 10)
        if w != answer and w > 0:
            wrong.add(w)
    
    options = list(wrong) + [answer]
    random.shuffle(options)
    
    builder = InlineKeyboardBuilder()
    for opt in options:
        builder.button(text=str(opt), callback_data=f"math_{opt}_{answer}_15")
    builder.button(text="⬅️ Orqaga", callback_data="back_games")
    builder.adjust(2, 2, 1)
    
    await callback.message.edit_text(
        f"🧮 *Matematika O'yini*\n\n*{a} {op} {b} = ?*\n\nTo'g'ri javobni tanlang!\n🎯 +15 coin",
        reply_markup=builder.as_markup(), parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("math_"))
async def math_answer(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    chosen = int(parts[1])
    correct = int(parts[2])
    reward = int(parts[3])
    
    user = get_user(callback.from_user.id)
    update_user(callback.from_user.id, {"games_played": user["games_played"] + 1})
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🧮 Yana o'yna", callback_data="game_math")
    builder.button(text="⬅️ Orqaga", callback_data="back_games")
    
    if chosen == correct:
        new_coins = add_coins(callback.from_user.id, reward)
        update_user(callback.from_user.id, {"wins": user["wins"] + 1})
        text = f"✅ *To'g'ri!* Javob: *{correct}*\n\n+{reward} coin! 🪙\nJami: *{new_coins} coin*"
    else:
        text = f"❌ *Noto'g'ri!* Javob: *{correct}* edi\n\nSen: {chosen}\n🪙 Coin: *{user['coins']}*"
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# ===== NAVIGATSIYA =====
@dp.callback_query(F.data == "back_games")
async def back_to_games(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎮 *Qaysi o'yinni tanlaysiz?*",
        reply_markup=games_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "back_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.delete()

@dp.callback_query(F.data == "cancel_game")
async def cancel_game(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎮 *Qaysi o'yinni tanlaysiz?*",
        reply_markup=games_keyboard(),
        parse_mode="Markdown"
    )

# ===== ADMIN BUYRUQLARI =====
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    db = load_db()
    total = len(db)
    total_games = sum(u.get("games_played", 0) for u in db.values())
    await message.answer(
        f"👑 *Admin Panel*\n\n👥 Jami foydalanuvchilar: *{total}*\n🎮 Jami o'yinlar: *{total_games}*",
        parse_mode="Markdown"
    )

@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("Xabar matnini kiriting: /broadcast [xabar]")
        return
    db = load_db()
    sent = 0
    for uid in db.keys():
        try:
            await bot.send_message(int(uid), text)
            sent += 1
        except:
            pass
    await message.answer(f"✅ {sent} ta foydalanuvchiga yuborildi!")

# ===== ISHGA TUSHIRISH =====
async def main():
    print("🎮 Game Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
