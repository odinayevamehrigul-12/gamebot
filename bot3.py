import telebot
import random
import json
import os
from telebot import types

BOT_TOKEN = "8745430772:AAEP5WmU6ZaY1RIvWwz5fz5sUPEYYKtBn5A"
bot = telebot.TeleBot(BOT_TOKEN)

# ===== KARTA TIZIMI =====
SUITS = {"♠️": "qora", "♥️": "qizil", "♦️": "qizil", "♣️": "qora"}
RANKS = ["6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {r: i for i, r in enumerate(RANKS)}

def make_deck():
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append(f"{rank}{suit}")
    random.shuffle(deck)
    return deck

def card_rank(card):
    rank = card[:-2] if len(card) > 3 else card[0]
    return RANK_VALUES.get(rank, 0)

def card_suit(card):
    return card[-2:]

def card_display(card):
    suit = card_suit(card)
    rank = card[:-2] if len(card) > 3 else card[0]
    colors = {"♠️": "⬛", "♥️": "🟥", "♦️": "🟧", "♣️": "🟩"}
    color = colors.get(suit, "⬜")
    return f"{color}{rank}{suit}"

# ===== O'YINLAR MA'LUMOTLARI =====
games = {}  # {chat_id: game_data}
waiting_rooms = {}  # {chat_id: room_data}

DB_FILE = "users.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, ensure_ascii=False)

def get_user(uid, name="O'yinchi"):
    db = load_db()
    uid = str(uid)
    if uid not in db:
        db[uid] = {"coins": 100, "wins": 0, "games": 0, "name": name}
        save_db(db)
    return db[uid]

def add_coins(uid, amount):
    db = load_db()
    uid = str(uid)
    if uid not in db:
        db[uid] = {"coins": 100, "wins": 0, "games": 0, "name": ""}
    db[uid]["coins"] = db[uid].get("coins", 100) + amount
    save_db(db)
    return db[uid]["coins"]

def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎮 O'yinlar", "💰 Balans")
    kb.row("🏆 Reyting", "👥 Taklif qil")
    return kb

def games_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("🃏 Durak", callback_data="game_durak"),
        types.InlineKeyboardButton("⚔️ Urush", callback_data="game_war")
    )
    kb.row(
        types.InlineKeyboardButton("🎭 Ko'r", callback_data="game_fool"),
        types.InlineKeyboardButton("🎲 Zar", callback_data="game_dice")
    )
    kb.row(
        types.InlineKeyboardButton("🪙 Tanga", callback_data="game_coin_start"),
        types.InlineKeyboardButton("🧮 Matematika", callback_data="game_math")
    )
    return kb

# ===== START =====
@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name or "O'yinchi"
    get_user(uid, name)
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

    user = get_user(uid)
    text = f"🎮 *Game Zone Botiga Xush Kelibsiz!*\n\nSalom, *{name}*! 👋\n🪙 Sizda: *{user['coins']} coin*\n\nO'yin tanlang! 👇"
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🎮 O'yinlar")
def show_games(message):
    bot.send_message(message.chat.id, "🎮 *Qaysi o'yinni tanlaysiz?*", reply_markup=games_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💰 Balans")
def balance(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id, f"💰 *Balansingiz*\n\n🪙 Coin: *{user['coins']}*\n🏆 G'alabalar: *{user.get('wins',0)}*\n🎮 O'yinlar: *{user.get('games',0)}*", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🏆 Reyting")
def rating(message):
    db = load_db()
    top = sorted(db.items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:10]
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    text = "🏆 *TOP 10 O'yinchilar*\n\n"
    for i, (uid, data) in enumerate(top):
        text += f"{medals[i]} {data.get('name','?')}: 🪙 {data.get('coins',0)}\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "👥 Taklif qil")
def referral(message):
    uid = message.from_user.id
    bot_info = bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={uid}"
    bot.send_message(message.chat.id, f"👥 *Referral*\n\nDo'stingizni taklif qiling:\n• Siz: +100 coin\n• Do'stingiz: +100 coin\n\n🔗 Havola:\n`{link}`", parse_mode="Markdown")

# ===== DURAK O'YINI =====
def durak_hand_text(hand):
    return " ".join([card_display(c) for c in hand])

def start_durak_game(chat_id, players):
    deck = make_deck()
    trump_card = deck[-1]
    trump_suit = card_suit(trump_card)
    
    hands = {}
    for pid in players:
        hands[pid] = [deck.pop(0) for _ in range(6)]
    
    # Kozir kartasiga qarab birinchi hujumchi
    attacker = players[0]
    defender = players[1]
    
    games[chat_id] = {
        "type": "durak",
        "players": players,
        "hands": hands,
        "deck": deck,
        "trump": trump_suit,
        "trump_card": trump_card,
        "attacker": attacker,
        "defender": defender,
        "table": [],  # [(attack_card, defense_card or None)]
        "phase": "attack",  # attack / defense / end
        "passed": [],
        "names": {}
    }
    
    db = load_db()
    for pid in players:
        games[chat_id]["names"][str(pid)] = db.get(str(pid), {}).get("name", "O'yinchi")
    
    # Har bir o'yinchiga kartalarini yuborish
    g = games[chat_id]
    trump_display = card_display(trump_card)
    
    for pid in players:
        hand_text = durak_hand_text(g["hands"][pid])
        role = "⚔️ Siz hujum qilasiz!" if pid == attacker else "🛡 Siz himoyalanasiz!"
        try:
            bot.send_message(pid, f"🃏 *Durak O'yini Boshlandi!*\n\n🎴 Kozir: {trump_display} ({trump_suit})\n\n{role}\n\n🖐 Sizning kartalaringiz:\n{hand_text}", parse_mode="Markdown")
        except:
            pass
    
    send_durak_status(chat_id)

def send_durak_status(chat_id):
    g = games.get(chat_id)
    if not g:
        return
    
    attacker = g["attacker"]
    defender = g["defender"]
    a_name = g["names"].get(str(attacker), "Hujumchi")
    d_name = g["names"].get(str(defender), "Himoyachi")
    
    table_text = ""
    if g["table"]:
        for i, (ac, dc) in enumerate(g["table"]):
            if dc:
                table_text += f"{card_display(ac)} ➡️ {card_display(dc)}\n"
            else:
                table_text += f"{card_display(ac)} ❓\n"
    else:
        table_text = "Bo'sh"
    
    status = f"🃏 *Durak O'yini*\n\n🎴 Kozir: {g['trump']}\n📦 Qoldiq: {len(g['deck'])} karta\n\n⚔️ Hujumchi: *{a_name}*\n🛡 Himoyachi: *{d_name}*\n\n📋 *Stol:*\n{table_text}"
    
    # Hujumchi klaviaturasi
    if g["phase"] == "attack":
        kb = types.InlineKeyboardMarkup()
        hand = g["hands"].get(attacker, [])
        row = []
        for i, card in enumerate(hand):
            row.append(types.InlineKeyboardButton(card_display(card), callback_data=f"durak_atk_{chat_id}_{i}"))
            if len(row) == 3:
                kb.row(*row)
                row = []
        if row:
            kb.row(*row)
        kb.row(types.InlineKeyboardButton("✅ Tugatdim", callback_data=f"durak_end_atk_{chat_id}"))
        
        try:
            bot.send_message(attacker, status + "\n\n⚔️ *Hujum qiling!*", reply_markup=kb, parse_mode="Markdown")
        except:
            pass
    
    elif g["phase"] == "defense":
        hand = g["hands"].get(defender, [])
        attack_card = None
        for ac, dc in g["table"]:
            if dc is None:
                attack_card = ac
                break
        
        if attack_card:
            kb = types.InlineKeyboardMarkup()
            row = []
            for i, card in enumerate(hand):
                row.append(types.InlineKeyboardButton(card_display(card), callback_data=f"durak_def_{chat_id}_{i}"))
                if len(row) == 3:
                    kb.row(*row)
                    row = []
            if row:
                kb.row(*row)
            kb.row(types.InlineKeyboardButton("❌ Olaman (kartalarni ol)", callback_data=f"durak_take_{chat_id}"))
            
            try:
                bot.send_message(defender, status + f"\n\n🛡 *Himoyalaning!*\n{card_display(attack_card)} ga javob bering!", reply_markup=kb, parse_mode="Markdown")
            except:
                pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("game_durak"))
def durak_menu(call):
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("🎮 Xona ochish (2-4 kishi)", callback_data="durak_create"))
    kb.row(types.InlineKeyboardButton("🔍 Xonaga kirish", callback_data="durak_join_menu"))
    kb.row(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_games"))
    bot.edit_message_text("🃏 *Durak O'yini*\n\nXona oching yoki mavjud xonaga kiring!", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "durak_create")
def durak_create(call):
    uid = call.from_user.id
    name = call.from_user.first_name or "O'yinchi"
    get_user(uid, name)
    
    room_id = str(uid)
    waiting_rooms[room_id] = {
        "host": uid,
        "players": [uid],
        "names": {uid: name},
        "game": "durak"
    }
    
    bot_info = bot.get_me()
    join_link = f"https://t.me/{bot_info.username}?start=join_{room_id}"
    
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("▶️ Boshlash (2+ kishi kerak)", callback_data=f"durak_start_{room_id}"))
    kb.row(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="durak_cancel"))
    
    bot.edit_message_text(
        f"🃏 *Durak Xonasi*\n\nXona ID: `{room_id}`\n\n👥 O'yinchilar (1/4):\n1. {name} 👑\n\nDo'stlaringizga bu havolani yuboring:\n`{join_link}`\n\n2-4 kishi to'planganida boshlang!",
        call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("durak_start_"))
def durak_start(call):
    room_id = call.data.replace("durak_start_", "")
    room = waiting_rooms.get(room_id)
    
    if not room:
        bot.answer_callback_query(call.id, "Xona topilmadi!")
        return
    
    if call.from_user.id != room["host"]:
        bot.answer_callback_query(call.id, "Faqat xona egasi boshlashi mumkin!")
        return
    
    if len(room["players"]) < 2:
        bot.answer_callback_query(call.id, "Kamida 2 kishi kerak!")
        return
    
    players = room["players"]
    chat_id = call.message.chat.id
    
    # Har bir o'yinchiga xabar
    for pid in players:
        try:
            bot.send_message(pid, "🃏 *Durak o'yini boshlanmoqda!*", parse_mode="Markdown")
        except:
            pass
    
    del waiting_rooms[room_id]
    start_durak_game(chat_id, players)

@bot.callback_query_handler(func=lambda c: c.data.startswith("durak_atk_"))
def durak_attack(call):
    parts = call.data.split("_")
    chat_id = int(parts[2])
    card_idx = int(parts[3])
    
    g = games.get(chat_id)
    if not g or g["phase"] != "attack":
        bot.answer_callback_query(call.id, "Hozir hujum qilish mumkin emas!")
        return
    
    if call.from_user.id != g["attacker"]:
        bot.answer_callback_query(call.id, "Siz hujumchi emassiz!")
        return
    
    hand = g["hands"][g["attacker"]]
    if card_idx >= len(hand):
        return
    
    card = hand[card_idx]
    
    # Stolga karta qo'yish
    if g["table"]:
        valid_ranks = set()
        for ac, dc in g["table"]:
            r = ac[:-2] if len(ac) > 3 else ac[0]
            valid_ranks.add(r)
            if dc:
                r2 = dc[:-2] if len(dc) > 3 else dc[0]
                valid_ranks.add(r2)
        
        card_r = card[:-2] if len(card) > 3 else card[0]
        if card_r not in valid_ranks:
            bot.answer_callback_query(call.id, "Bu kartani qo'yib bo'lmaydi! Faqat bir xil qiymatli karta qo'ying!")
            return
    
    hand.pop(card_idx)
    g["table"].append((card, None))
    g["phase"] = "defense"
    
    bot.answer_callback_query(call.id, f"{card_display(card)} qo'yildi!")
    send_durak_status(chat_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("durak_def_"))
def durak_defense(call):
    parts = call.data.split("_")
    chat_id = int(parts[2])
    card_idx = int(parts[3])
    
    g = games.get(chat_id)
    if not g or g["phase"] != "defense":
        bot.answer_callback_query(call.id, "Hozir himoya qilish mumkin emas!")
        return
    
    if call.from_user.id != g["defender"]:
        bot.answer_callback_query(call.id, "Siz himoyachi emassiz!")
        return
    
    hand = g["hands"][g["defender"]]
    if card_idx >= len(hand):
        return
    
    def_card = hand[card_idx]
    
    # Hujum kartasini topish
    atk_idx = None
    atk_card = None
    for i, (ac, dc) in enumerate(g["table"]):
        if dc is None:
            atk_idx = i
            atk_card = ac
            break
    
    if atk_card is None:
        return
    
    # Himoya karta to'g'riligini tekshirish
    atk_suit = card_suit(atk_card)
    def_suit = card_suit(def_card)
    trump = g["trump"]
    
    valid = False
    if def_suit == atk_suit and card_rank(def_card) > card_rank(atk_card):
        valid = True
    elif def_suit == trump and atk_suit != trump:
        valid = True
    
    if not valid:
        bot.answer_callback_query(call.id, "Bu karta bilan himoyalanib bo'lmaydi!")
        return
    
    hand.pop(card_idx)
    g["table"][atk_idx] = (atk_card, def_card)
    g["phase"] = "attack"
    
    # Himoyalanmagan karta qoldimi?
    undefended = any(dc is None for _, dc in g["table"])
    if not undefended:
        # Barcha kartalar himoyalangan
        bot.answer_callback_query(call.id, f"✅ {card_display(def_card)} bilan himoyalandingiz!")
        # Stolni tozalash
        g["table"] = []
        g["phase"] = "attack"
        
        # Kartalarni to'ldirish
        refill_hands(chat_id)
        check_winner(chat_id)
    else:
        bot.answer_callback_query(call.id, f"{card_display(def_card)} qo'yildi!")
        send_durak_status(chat_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("durak_take_"))
def durak_take(call):
    chat_id = int(call.data.replace("durak_take_", ""))
    g = games.get(chat_id)
    
    if not g:
        return
    
    if call.from_user.id != g["defender"]:
        bot.answer_callback_query(call.id, "Siz himoyachi emassiz!")
        return
    
    # Barcha stoldan kartalarni olish
    defender = g["defender"]
    for ac, dc in g["table"]:
        g["hands"][defender].append(ac)
        if dc:
            g["hands"][defender].append(dc)
    
    g["table"] = []
    
    # Navbat o'zgartirish (himoyachi o'tkazib yuboradi)
    players = g["players"]
    atk_idx = players.index(g["attacker"])
    def_idx = players.index(g["defender"])
    
    new_atk_idx = (def_idx + 1) % len(players)
    new_def_idx = (new_atk_idx + 1) % len(players)
    
    g["attacker"] = players[new_atk_idx]
    g["defender"] = players[new_def_idx]
    g["phase"] = "attack"
    
    bot.answer_callback_query(call.id, "Kartalarni oldingiz!")
    
    for pid in g["players"]:
        d_name = g["names"].get(str(defender), "Himoyachi")
        try:
            bot.send_message(pid, f"❌ *{d_name} kartalarni oldi!*\n\nNavbat o'zgardi.", parse_mode="Markdown")
        except:
            pass
    
    refill_hands(chat_id)
    send_durak_status(chat_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("durak_end_atk_"))
def durak_end_attack(call):
    chat_id = int(call.data.replace("durak_end_atk_", ""))
    g = games.get(chat_id)
    
    if not g or g["phase"] != "attack":
        return
    
    if call.from_user.id != g["attacker"]:
        bot.answer_callback_query(call.id, "Siz hujumchi emassiz!")
        return
    
    if not g["table"]:
        bot.answer_callback_query(call.id, "Kamida 1 ta karta qo'ying!")
        return
    
    # Himoyalanmagan karta bormi?
    undefended = any(dc is None for _, dc in g["table"])
    if undefended:
        bot.answer_callback_query(call.id, "Himoyachi hali javob bermadi!")
        return
    
    # Stolni tozalash, navbat o'zgartirish
    g["table"] = []
    players = g["players"]
    atk_idx = players.index(g["attacker"])
    def_idx = players.index(g["defender"])
    
    new_atk_idx = (atk_idx + 1) % len(players)
    new_def_idx = (new_atk_idx + 1) % len(players)
    
    g["attacker"] = players[new_atk_idx]
    g["defender"] = players[new_def_idx]
    g["phase"] = "attack"
    
    bot.answer_callback_query(call.id, "✅ Tugatdingiz!")
    refill_hands(chat_id)
    check_winner(chat_id)
    if chat_id in games:
        send_durak_status(chat_id)

def refill_hands(chat_id):
    g = games.get(chat_id)
    if not g:
        return
    
    for pid in g["players"]:
        while len(g["hands"][pid]) < 6 and g["deck"]:
            g["hands"][pid].append(g["deck"].pop(0))

def check_winner(chat_id):
    g = games.get(chat_id)
    if not g:
        return
    
    # Qo'lida karta qolmagan o'yinchilar
    finished = [pid for pid in g["players"] if len(g["hands"][pid]) == 0 and len(g["deck"]) == 0]
    
    if len(finished) >= len(g["players"]) - 1:
        # O'yin tugadi
        remaining = [pid for pid in g["players"] if len(g["hands"][pid]) > 0]
        
        if remaining:
            loser = remaining[0]
            loser_name = g["names"].get(str(loser), "O'yinchi")
            
            for pid in g["players"]:
                if pid != loser:
                    add_coins(pid, 50)
                    name = g["names"].get(str(pid), "O'yinchi")
                    try:
                        bot.send_message(pid, f"🏆 *{name} yutdi!* +50 coin\n\n🤡 Durak: *{loser_name}*", parse_mode="Markdown")
                    except:
                        pass
                else:
                    try:
                        bot.send_message(pid, f"🤡 *Siz Durak bo'ldingiz!*\n\nKeyingi safar omad!", parse_mode="Markdown")
                    except:
                        pass
            
            del games[chat_id]

@bot.callback_query_handler(func=lambda c: c.data == "durak_cancel")
def durak_cancel(call):
    uid = call.from_user.id
    room_id = str(uid)
    if room_id in waiting_rooms:
        del waiting_rooms[room_id]
    bot.edit_message_text("❌ Xona bekor qilindi.", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data == "durak_join_menu")
def durak_join_menu(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🔍 Xona ID sini yuboring:")
    bot.register_next_step_handler(msg, process_join_room)

def process_join_room(message):
    room_id = message.text.strip()
    uid = message.from_user.id
    name = message.from_user.first_name or "O'yinchi"
    
    if room_id not in waiting_rooms:
        bot.send_message(message.chat.id, "❌ Xona topilmadi!")
        return
    
    room = waiting_rooms[room_id]
    
    if uid in room["players"]:
        bot.send_message(message.chat.id, "❌ Siz allaqachon bu xonasizda!")
        return
    
    if len(room["players"]) >= 4:
        bot.send_message(message.chat.id, "❌ Xona to'la (4/4)!")
        return
    
    room["players"].append(uid)
    room["names"][uid] = name
    
    players_text = ""
    for i, pid in enumerate(room["players"]):
        pname = room["names"].get(pid, "O'yinchi")
        crown = " 👑" if pid == room["host"] else ""
        players_text += f"{i+1}. {pname}{crown}\n"
    
    bot.send_message(message.chat.id, f"✅ *Xonaga kirdingiz!*\n\n👥 O'yinchilar ({len(room['players'])}/4):\n{players_text}\nXona egasi o'yinni boshlaguniga kuting...", parse_mode="Markdown")
    
    # Xona egasiga xabar
    try:
        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton(f"▶️ Boshlash ({len(room['players'])} kishi)", callback_data=f"durak_start_{room_id}"))
        kb.row(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="durak_cancel"))
        
        bot.send_message(room["host"], f"👥 *{name} xonaga kirdi!*\n\nO'yinchilar ({len(room['players'])}/4):\n{players_text}", reply_markup=kb, parse_mode="Markdown")
    except:
        pass

# ===== URUSH O'YINI (Ko'p o'yinchi) =====
war_games = {}

@bot.callback_query_handler(func=lambda c: c.data == "game_war")
def war_menu(call):
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("⚔️ Xona ochish", callback_data="war_create"))
    kb.row(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_games"))
    bot.edit_message_text("⚔️ *Urush O'yini*\n\n36 ta karta bilan o'ynang!\nHar raundda karta olib, katta karta yutadi!\n\n2-4 kishi o'ynashi mumkin.", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "war_create")
def war_create(call):
    uid = call.from_user.id
    name = call.from_user.first_name or "O'yinchi"
    get_user(uid, name)
    
    room_id = f"war_{uid}"
    waiting_rooms[room_id] = {
        "host": uid,
        "players": [uid],
        "names": {uid: name},
        "game": "war"
    }
    
    bot_info = bot.get_me()
    join_link = f"https://t.me/{bot_info.username}?start=join_{room_id}"
    
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("▶️ Boshlash", callback_data=f"war_start_{room_id}"))
    kb.row(types.InlineKeyboardButton("❌ Bekor", callback_data=f"war_cancel_{room_id}"))
    
    bot.edit_message_text(
        f"⚔️ *Urush Xonasi*\n\nXona ID: `{room_id}`\n\n👥 O'yinchilar (1/4):\n1. {name} 👑\n\nHavola:\n`{join_link}`",
        call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("war_start_"))
def war_start(call):
    room_id = call.data.replace("war_start_", "")
    room = waiting_rooms.get(room_id)
    
    if not room or len(room["players"]) < 2:
        bot.answer_callback_query(call.id, "Kamida 2 kishi kerak!")
        return
    
    players = room["players"]
    deck = make_deck()
    
    # Kartalarni taqsimlash
    hands = {pid: [] for pid in players}
    while deck:
        for pid in players:
            if deck:
                hands[pid].append(deck.pop(0))
    
    war_games[room_id] = {
        "players": players,
        "names": room["names"],
        "hands": hands,
        "round": 0,
        "scores": {pid: 0 for pid in players}
    }
    
    del waiting_rooms[room_id]
    
    # Har bir o'yinchiga xabar
    for pid in players:
        hand_count = len(hands[pid])
        try:
            bot.send_message(pid, f"⚔️ *Urush O'yini Boshlandi!*\n\nSizda {hand_count} ta karta bor!\nHar raundda katta karta yutadi!", parse_mode="Markdown")
        except:
            pass
    
    play_war_round(room_id, call.message.chat.id)

def play_war_round(room_id, chat_id):
    g = war_games.get(room_id)
    if not g:
        return
    
    g["round"] += 1
    
    # Har bir o'yinchi 1 ta karta tashlaydi
    round_cards = {}
    for pid in g["players"]:
        if g["hands"][pid]:
            card = g["hands"][pid].pop(0)
            round_cards[pid] = card
    
    if not round_cards:
        end_war_game(room_id, chat_id)
        return
    
    # G'olibni aniqlash
    winner = max(round_cards, key=lambda p: card_rank(round_cards[p]))
    winner_card = round_cards[winner]
    winner_name = g["names"].get(winner, "O'yinchi")
    g["scores"][winner] = g["scores"].get(winner, 0) + 1
    
    # Natija matni
    result = f"⚔️ *{g['round']}-raund*\n\n"
    for pid, card in round_cards.items():
        name = g["names"].get(pid, "O'yinchi")
        crown = " 🏆" if pid == winner else ""
        result += f"{name}: {card_display(card)}{crown}\n"
    
    result += f"\n🥇 *{winner_name} yutdi!*"
    
    # Kartalar qoldimi?
    has_cards = any(len(g["hands"][pid]) > 0 for pid in g["players"])
    
    kb = types.InlineKeyboardMarkup()
    if has_cards:
        kb.row(types.InlineKeyboardButton("▶️ Keyingi raund", callback_data=f"war_next_{room_id}_{chat_id}"))
        kb.row(types.InlineKeyboardButton("🏳️ Tugatish", callback_data=f"war_end_{room_id}_{chat_id}"))
    else:
        kb.row(types.InlineKeyboardButton("🏆 Natijalar", callback_data=f"war_end_{room_id}_{chat_id}"))
    
    try:
        bot.send_message(chat_id, result, reply_markup=kb, parse_mode="Markdown")
    except:
        # Shaxsiy xabarga yuborish
        for pid in g["players"]:
            try:
                bot.send_message(pid, result, reply_markup=kb, parse_mode="Markdown")
                break
            except:
                pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("war_next_"))
def war_next(call):
    parts = call.data.split("_")
    room_id = f"war_{parts[2]}"
    chat_id = int(parts[3])
    play_war_round(room_id, chat_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("war_end_"))
def war_end(call):
    parts = call.data.split("_")
    room_id = f"war_{parts[2]}"
    chat_id = int(parts[3])
    end_war_game(room_id, chat_id)

def end_war_game(room_id, chat_id):
    g = war_games.get(room_id)
    if not g:
        return
    
    scores = g["scores"]
    winner = max(scores, key=scores.get)
    winner_name = g["names"].get(winner, "O'yinchi")
    
    result = "🏆 *O'yin Tugadi!*\n\n📊 *Natijalar:*\n"
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    medals = ["🥇", "🥈", "🥉", "4️⃣"]
    
    for i, (pid, score) in enumerate(sorted_scores):
        name = g["names"].get(pid, "O'yinchi")
        result += f"{medals[i]} {name}: {score} raund\n"
        if pid == winner:
            add_coins(pid, 30)
    
    result += f"\n🎉 *G'olib: {winner_name}!* +30 coin"
    
    for pid in g["players"]:
        try:
            bot.send_message(pid, result, parse_mode="Markdown")
        except:
            pass
    
    if room_id in war_games:
        del war_games[room_id]

@bot.callback_query_handler(func=lambda c: c.data.startswith("war_cancel_"))
def war_cancel(call):
    room_id = call.data.replace("war_cancel_", "")
    if room_id in waiting_rooms:
        del waiting_rooms[room_id]
    bot.edit_message_text("❌ Xona bekor qilindi.", call.message.chat.id, call.message.message_id)

# ===== KO'R O'YINI =====
@bot.callback_query_handler(func=lambda c: c.data == "game_fool")
def fool_game(call):
    bot.answer_callback_query(call.id, "🎭 Ko'r o'yini tez kunda qo'shiladi!")

# ===== ZAR =====
@bot.callback_query_handler(func=lambda c: c.data == "game_dice")
def dice_game(call):
    p = random.randint(1, 6)
    c = random.randint(1, 6)
    dice = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣"]
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("🎲 Yana", callback_data="game_dice"),
           types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_games"))
    if p > c:
        coins = add_coins(call.from_user.id, 15)
        text = f"🎲 *Zar*\n\n👤 {dice[p-1]}\n💻 {dice[c-1]}\n\n🎉 +15 coin! 🪙{coins}"
    elif p < c:
        user = get_user(call.from_user.id)
        text = f"🎲 *Zar*\n\n👤 {dice[p-1]}\n💻 {dice[c-1]}\n\n😔 Bot yutdi"
    else:
        coins = add_coins(call.from_user.id, 5)
        text = f"🎲 *Zar*\n\n👤 {dice[p-1]}\n💻 {dice[c-1]}\n\n🤝 Durrang! +5 coin 🪙{coins}"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

# ===== TANGA =====
@bot.callback_query_handler(func=lambda c: c.data == "game_coin_start")
def coin_start(call):
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("🟡 Toq", callback_data="coin_odd"),
           types.InlineKeyboardButton("⚪ Juft", callback_data="coin_even"))
    kb.row(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_games"))
    bot.edit_message_text("🪙 *Tanga*\n\nToq yoki Juft? +10 coin", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data in ["coin_odd", "coin_even"])
def coin_result(call):
    result = random.choice(["odd", "even"])
    choice = "odd" if call.data == "coin_odd" else "even"
    res_text = "🟡 Toq" if result == "odd" else "⚪ Juft"
    ch_text = "🟡 Toq" if choice == "odd" else "⚪ Juft"
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("🪙 Yana", callback_data="game_coin_start"),
           types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_games"))
    if choice == result:
        coins = add_coins(call.from_user.id, 10)
        text = f"🪙 *Tanga*\n\nSen: {ch_text}\nNatija: {res_text}\n\n🎉 +10 coin! 🪙{coins}"
    else:
        user = get_user(call.from_user.id)
        text = f"🪙 *Tanga*\n\nSen: {ch_text}\nNatija: {res_text}\n\n😔 Noto'g'ri!"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

# ===== MATEMATIKA =====
@bot.callback_query_handler(func=lambda c: c.data == "game_math")
def math_game(call):
    ops = ["+", "-", "x"]
    op = random.choice(ops)
    if op == "+":
        a, b = random.randint(1,50), random.randint(1,50)
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
    kb = types.InlineKeyboardMarkup()
    row1 = [types.InlineKeyboardButton(str(o), callback_data=f"math_{o}_{ans}") for o in options[:2]]
    row2 = [types.InlineKeyboardButton(str(o), callback_data=f"math_{o}_{ans}") for o in options[2:]]
    kb.row(*row1)
    kb.row(*row2)
    kb.row(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_games"))
    bot.edit_message_text(f"🧮 *Matematika*\n\n*{a} {op} {b} = ?*\n\n+15 coin", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("math_"))
def math_answer(call):
    parts = call.data.split("_")
    chosen, correct = int(parts[1]), int(parts[2])
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("🧮 Yana", callback_data="game_math"),
           types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_games"))
    if chosen == correct:
        coins = add_coins(call.from_user.id, 15)
        text = f"✅ *To'g'ri!* Javob: *{correct}*\n+15 coin! 🪙{coins}"
    else:
        text = f"❌ *Noto'g'ri!* Javob: *{correct}* edi"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

# ===== NAVIGATSIYA =====
@bot.callback_query_handler(func=lambda c: c.data == "back_games")
def back_games(call):
    bot.edit_message_text("🎮 *Qaysi o'yinni tanlaysiz?*", call.message.chat.id, call.message.message_id, reply_markup=games_keyboard(), parse_mode="Markdown")

# ===== START (join link) =====
@bot.message_handler(commands=["start"])
def handle_join(message):
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("join_"):
        room_id = args[1].replace("join_", "")
        uid = message.from_user.id
        name = message.from_user.first_name or "O'yinchi"
        
        if room_id in waiting_rooms:
            room = waiting_rooms[room_id]
            if uid not in room["players"] and len(room["players"]) < 4:
                room["players"].append(uid)
                room["names"][uid] = name
                
                players_text = ""
                for i, pid in enumerate(room["players"]):
                    pname = room["names"].get(pid, "O'yinchi")
                    crown = " 👑" if pid == room["host"] else ""
                    players_text += f"{i+1}. {pname}{crown}\n"
                
                bot.send_message(message.chat.id, f"✅ *Xonaga kirdingiz!*\n\n👥 ({len(room['players'])}/4):\n{players_text}\nEga boshlaguniga kuting...", parse_mode="Markdown")
                
                try:
                    game_type = room.get("game", "durak")
                    kb = types.InlineKeyboardMarkup()
                    if game_type == "durak":
                        kb.row(types.InlineKeyboardButton(f"▶️ Boshlash ({len(room['players'])} kishi)", callback_data=f"durak_start_{room_id}"))
                    else:
                        kb.row(types.InlineKeyboardButton(f"▶️ Boshlash ({len(room['players'])} kishi)", callback_data=f"war_start_{room_id}"))
                    bot.send_message(room["host"], f"👥 *{name} xonaga kirdi!*\n\n({len(room['players'])}/4):\n{players_text}", reply_markup=kb, parse_mode="Markdown")
                except:
                    pass

print("🎮 PlayZone Bot (Yangilangan) ishga tushdi!")
bot.infinity_polling()
