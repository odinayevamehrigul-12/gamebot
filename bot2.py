import telebot
import random
import json
import os

BOT_TOKEN = "8745430772:AAEP5WmU6ZaY1RIvWwz5fz5sUPEYYKtBn5A"
bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "users.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

def get_user(uid):
    db = load_db()
    uid = str(uid)
    if uid not in db:
        db[uid] = {"coins": 100, "wins": 0, "games": 0, "name": ""}
        save_db(db)
    return db[uid]

def add_coins(uid, amount):
    db = load_db()
    uid = str(uid)
    if uid not in db:
        db[uid] = {"coins": 100, "wins": 0, "games": 0, "name": ""}
    db[uid]["coins"] += amount
    save_db(db)
    return db[uid]["coins"]

def main_keyboard():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎮 O'yinlar", "💰 Balans")
    kb.row("🏆 Reyting", "👥 Taklif qil")
    return kb

def games_keyboard():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(
        telebot.types.InlineKeyboardButton("🃏 Karta", callback_data="game_card"),
        telebot.types.InlineKeyboardButton("🎲 Zar", callback_data="game_dice")
    )
    kb.row(
        telebot.types.InlineKeyboardButton("🪙 Tanga", callback_data="game_coin_start"),
        telebot.types.InlineKeyboardButton("🔢 Son top", callback_data="game_guess")
    )
    kb.row(
        telebot.types.InlineKeyboardButton("🧮 Matematika", callback_data="game_math")
    )
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name or "O'yinchi"
    user = get_user(uid)
    db = load_db()
    db[str(uid)]["name"] = name
    save_db(db)

    args = message.text.split()
    if len(args) > 1 and args[1].isdigit() and int(args[1]) != uid:
        ref_id = args[1]
        add_coins(int(ref_id), 100)
        try:
            bot.send_message(int(ref_id), f"🎉 Do'stingiz {name} qo'shildi! +100 coin!")
        except:
            pass

    text = f"""🎮 *Game Zone Botiga Xush Kelibsiz!*

Salom, *{name}*! 👋
🪙 Sizda: *{user['coins']} coin*

O'yin tanlang! 👇"""
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🎮 O'yinlar")
def show_games(message):
    bot.send_message(message.chat.id, "🎮 Qaysi o'yinni tanlaysiz?", reply_markup=games_keyboard())

@bot.message_handler(func=lambda m: m.text == "💰 Balans")
def balance(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id, f"💰 *Balansingiz*\n\n🪙 Coin: *{user['coins']}*\n🏆 G'alabalar: *{user['wins']}*\n🎮 O'yinlar: *{user['games']}*", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🏆 Reyting")
def rating(message):
    db = load_db()
    top = sorted(db.items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:10]
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    text = "🏆 *TOP 10*\n\n"
    for i, (uid, data) in enumerate(top):
        text += f"{medals[i]} {data.get('name','?')}: 🪙 {data.get('coins',0)}\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "👥 Taklif qil")
def referral(message):
    uid = message.from_user.id
    bot_info = bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={uid}"
    bot.send_message(message.chat.id, f"👥 *Referral*\n\nDo'stingizni taklif qiling:\n• Siz: +100 coin\n• Do'stingiz: +100 coin\n\n🔗 Havola:\n`{link}`", parse_mode="Markdown")

# KARTA
@bot.callback_query_handler(func=lambda c: c.data == "game_card")
def card_game(call):
    suits = ["♠️","♥️","♦️","♣️"]
    vals = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
    p = random.choice(vals) + random.choice(suits)
    c = random.choice(vals) + random.choice(suits)
    pr = vals.index(p[:-2] if len(p)>2 else p[0])
    cr = vals.index(c[:-2] if len(c)>2 else c[0])

    db = load_db()
    uid = str(call.from_user.id)
    if uid not in db:
        get_user(call.from_user.id)
    db[uid]["games"] = db[uid].get("games", 0) + 1
    save_db(db)

    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(telebot.types.InlineKeyboardButton("🃏 Yana", callback_data="game_card"),
           telebot.types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_games"))

    if pr > cr:
        coins = add_coins(call.from_user.id, 20)
        db2 = load_db()
        db2[uid]["wins"] = db2[uid].get("wins", 0) + 1
        save_db(db2)
        text = f"🃏 *Karta O'yini*\n\n👤 Sen: *{p}*\n💻 Bot: *{c}*\n\n🎉 *Sen yutding!* +20 coin\n🪙 {coins}"
    elif pr < cr:
        text = f"🃏 *Karta O'yini*\n\n👤 Sen: *{p}*\n💻 Bot: *{c}*\n\n😔 *Bot yutdi...*"
    else:
        coins = add_coins(call.from_user.id, 5)
        text = f"🃏 *Karta O'yini*\n\n👤 Sen: *{p}*\n💻 Bot: *{c}*\n\n🤝 *Durrang!* +5 coin\n🪙 {coins}"

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

# ZAR
@bot.callback_query_handler(func=lambda c: c.data == "game_dice")
def dice_game(call):
    p = random.randint(1, 6)
    c = random.randint(1, 6)
    dice = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣"]

    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(telebot.types.InlineKeyboardButton("🎲 Yana", callback_data="game_dice"),
           telebot.types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_games"))

    if p > c:
        coins = add_coins(call.from_user.id, 15)
        text = f"🎲 *Zar O'yini*\n\n👤 Sen: {dice[p-1]}\n💻 Bot: {dice[c-1]}\n\n🎉 *Sen yutding!* +15 coin\n🪙 {coins}"
    elif p < c:
        user = get_user(call.from_user.id)
        text = f"🎲 *Zar O'yini*\n\n👤 Sen: {dice[p-1]}\n💻 Bot: {dice[c-1]}\n\n😔 *Bot yutdi...*"
    else:
        coins = add_coins(call.from_user.id, 5)
        text = f"🎲 *Zar O'yini*\n\n👤 Sen: {dice[p-1]}\n💻 Bot: {dice[c-1]}\n\n🤝 *Durrang!* +5 coin\n🪙 {coins}"

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

# TANGA
@bot.callback_query_handler(func=lambda c: c.data == "game_coin_start")
def coin_start(call):
    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(telebot.types.InlineKeyboardButton("🟡 Toq", callback_data="coin_odd"),
           telebot.types.InlineKeyboardButton("⚪ Juft", callback_data="coin_even"))
    kb.row(telebot.types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_games"))
    bot.edit_message_text("🪙 *Tanga O'yini*\n\nToq yoki Juft tanlang!\n🎯 To'g'ri topsangiz: +10 coin",
                          call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data in ["coin_odd", "coin_even"])
def coin_result(call):
    result = random.choice(["odd", "even"])
    choice = "odd" if call.data == "coin_odd" else "even"
    res_text = "🟡 Toq" if result == "odd" else "⚪ Juft"
    ch_text = "🟡 Toq" if choice == "odd" else "⚪ Juft"

    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(telebot.types.InlineKeyboardButton("🪙 Yana", callback_data="game_coin_start"),
           telebot.types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_games"))

    if choice == result:
        coins = add_coins(call.from_user.id, 10)
        text = f"🪙 *Tanga*\n\nSen: {ch_text}\nNatija: {res_text}\n\n🎉 *To'g'ri!* +10 coin\n🪙 {coins}"
    else:
        user = get_user(call.from_user.id)
        text = f"🪙 *Tanga*\n\nSen: {ch_text}\nNatija: {res_text}\n\n😔 *Noto'g'ri!*\n🪙 {user['coins']}"

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

# MATEMATIKA
@bot.callback_query_handler(func=lambda c: c.data == "game_math")
def math_game(call):
    ops = ["+", "-", "x"]
    op = random.choice(ops)
    if op == "+":
        a, b, ans = random.randint(1,50), random.randint(1,50), 0
        ans = a + b
    elif op == "-":
        a, b = random.randint(10,50), random.randint(1,9)
        ans = a - b
    else:
        a, b = random.randint(2,9), random.randint(2,9)
        ans = a * b

    wrong = set()
    while len(wrong) < 3:
        w = ans + random.randint(-10, 10)
        if w != ans and w > 0:
            wrong.add(w)

    options = list(wrong) + [ans]
    random.shuffle(options)

    kb = telebot.types.InlineKeyboardMarkup()
    row1 = [telebot.types.InlineKeyboardButton(str(o), callback_data=f"math_{o}_{ans}") for o in options[:2]]
    row2 = [telebot.types.InlineKeyboardButton(str(o), callback_data=f"math_{o}_{ans}") for o in options[2:]]
    kb.row(*row1)
    kb.row(*row2)
    kb.row(telebot.types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_games"))

    bot.edit_message_text(f"🧮 *Matematika*\n\n*{a} {op} {b} = ?*\n\nTo'g'ri javobni tanlang! 🎯 +15 coin",
                          call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("math_"))
def math_answer(call):
    parts = call.data.split("_")
    chosen, correct = int(parts[1]), int(parts[2])

    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(telebot.types.InlineKeyboardButton("🧮 Yana", callback_data="game_math"),
           telebot.types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_games"))

    if chosen == correct:
        coins = add_coins(call.from_user.id, 15)
        text = f"✅ *To'g'ri!* Javob: *{correct}*\n+15 coin! 🪙 {coins}"
    else:
        user = get_user(call.from_user.id)
        text = f"❌ *Noto'g'ri!* Javob: *{correct}* edi\n🪙 {user['coins']}"

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

# SON TOPISH
user_guess = {}

@bot.callback_query_handler(func=lambda c: c.data == "game_guess")
def guess_start(call):
    uid = call.from_user.id
    user_guess[uid] = {"secret": random.randint(1,100), "attempts": 0}
    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(telebot.types.InlineKeyboardButton("❌ Bekor", callback_data="back_games"))
    bot.edit_message_text("🔢 *Sonni Top!*\n\n1-100 orasida son o'yladim...\nSon yuboring! (7 urinish)\n\n+10-30 coin",
                          call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.from_user.id in user_guess)
def guess_check(message):
    uid = message.from_user.id
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "❗ Faqat son kiriting!")
        return
    g = int(message.text)
    if g < 1 or g > 100:
        bot.send_message(message.chat.id, "❗ 1-100 orasida son kiriting!")
        return

    secret = user_guess[uid]["secret"]
    user_guess[uid]["attempts"] += 1
    att = user_guess[uid]["attempts"]
    left = 7 - att

    kb = telebot.types.InlineKeyboardMarkup()

    if g == secret:
        coins_won = max(30 - att*3, 5)
        coins = add_coins(uid, coins_won)
        del user_guess[uid]
        kb.row(telebot.types.InlineKeyboardButton("🔢 Yana", callback_data="game_guess"))
        bot.send_message(message.chat.id, f"🎉 *To'g'ri!* Son *{secret}* edi!\n{att} urinishda topdingiz!\n+{coins_won} coin! 🪙 {coins}", reply_markup=kb, parse_mode="Markdown")
    elif att >= 7:
        del user_guess[uid]
        kb.row(telebot.types.InlineKeyboardButton("🔢 Yana", callback_data="game_guess"))
        bot.send_message(message.chat.id, f"😔 Tugadi! Javob: *{secret}*", reply_markup=kb, parse_mode="Markdown")
    elif g < secret:
        bot.send_message(message.chat.id, f"⬆️ Kattaroq! ({left} urinish qoldi)")
    else:
        bot.send_message(message.chat.id, f"⬇️ Kichikroq! ({left} urinish qoldi)")

# NAVIGATSIYA
@bot.callback_query_handler(func=lambda c: c.data == "back_games")
def back_games(call):
    bot.edit_message_text("🎮 Qaysi o'yinni tanlaysiz?", call.message.chat.id, call.message.message_id, reply_markup=games_keyboard())

print("🎮 PlayZone Bot ishga tushdi!")
bot.infinity_polling()
