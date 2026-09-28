import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InlineQueryResultCachedSticker, InputTextMessageContent
from telegram.ext import ApplicationBuilder, CommandHandler, InlineQueryHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

game_session = {
    "active": False,
    "players": {},
    "player_order": [],
    "hands": {},
    "board": [],
    "stockpile": [],     # မဝေရသေးဘဲ ထပ်ဆွဲရန်ကျန်ရှိသော အတုံးများ
    "current_turn": 0,
    "chat_id": None,
    "sticker_mapping": {}
}

def create_dominoes():
    dominoes = []
    for i in range(7):
        for j in range(i, 7):
            dominoes.append((i, j))
    return dominoes

async def load_sticker_set(context: ContextTypes.DEFAULT_TYPE):
    try:
        sticker_set = await context.bot.get_sticker_set("DominoSO")
        stickers = sticker_set.stickers
        dominoes = create_dominoes()
        
        game_session["sticker_mapping"] = {}
        for idx, domino in enumerate(dominoes):
            if idx < len(stickers):
                game_session["sticker_mapping"][domino] = stickers[idx].file_id
        print("✅ Sticker Set အောင်မြင်စွာ ချိတ်ဆက်ပြီးပါပြီ။")
    except Exception as e:
        print(f"❌ Sticker Set ဆွဲယူရာတွင် အမှားရှိသည်: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("မင်္ဂလာပါ! Dominoes Bot (Sticker Mode) မှ ကြိုဆိုပါတယ်။ ဂိမ်းစဖို့ /newgame လို့ ရိုက်ပါ။")

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if game_session["active"]:
        await update.message.reply_text("⚠️ ဂိမ်းတစ်ခု လက်ရှိစတင်နေပါပြီ။ /join ဖြင့် ဝင်ရောက်ပါ။")
        return

    await load_sticker_set(context)

    game_session["active"] = True
    game_session["players"] = {}
    game_session["player_order"] = []
    game_session["hands"] = {}
    game_session["board"] = []
    game_session["stockpile"] = []
    game_session["current_turn"] = 0
    game_session["chat_id"] = update.effective_chat.id

    await update.message.reply_text(
        "🎲 Dominoes ဂိမ်းအခန်း စတင်လိုက်ပါပြီ!\n"
        "ကစားချင်သူများက /join လို့ ရိုက်ပြီး ဝင်ရောက်ပါ။\n"
        "အားလုံးဝင်ပြီးရင် /startgame လို့ ရိုက်ပါ။"
    )

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not game_session["active"]:
        await update.message.reply_text("❌ လက်ရှိ ဖွင့်ထားသော ဂိမ်းမရှိပါ။")
        return

    user = update.effective_user
    if user.id in game_session["players"]:
        await update.message.reply_text(f"{user.first_name}, သင် ဝင်ထားပြီးသား ဖြစ်ပါတယ်။")
        return

    game_session["players"][user.id] = user.first_name
    game_session["player_order"].append(user.id)
    await update.message.reply_text(f"✅ {user.first_name} ဂိမ်းထဲသို့ ဝင်ရောက်လာပါပြီ!")

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not game_session["active"]:
        await update.message.reply_text("❌ ဂိမ်းမစရသေးပါ။")
        return

    if len(game_session["player_order"]) < 1:
        await update.message.reply_text("⚠️ ကစားသမား အနည်းဆုံး ၁ ဦး လိုအပ်ပါသည်။")
        return

    dominoes = create_dominoes()
    random.shuffle(dominoes)

    game_session["board"] = []
    game_session["current_turn"] = 0

    for player_id in game_session["player_order"]:
        game_session["hands"][player_id] = [dominoes.pop() for _ in range(7)]
    
    # ကျန်ရှိသော အတုံးများကို stockpile (ဆွဲရန်ပုံ) အဖြစ် သိမ်းမည်
    game_session["stockpile"] = dominoes

    await send_turn_message(context)

async def send_turn_message(context: ContextTypes.DEFAULT_TYPE):
    current_player_id = game_session["player_order"][game_session["current_turn"]]
    current_player_name = game_session["players"][current_player_id]

    board = game_session["board"]
    if not board:
        board_str = "📭 ဘုတ်ပေါ်တွင် အတုံးမရှိသေးပါ (မည်သည့်တုံးမဆို ချနိုင်သည်)"
    else:
        board_str = f"[{board[0][0]}|{board[0][1]}] ... [{board[-1][0]}|{board[-1][1]}]"

    keyboard = [
        [InlineKeyboardButton("Make your choice!", switch_inline_query_current_chat="")],
        [
            InlineKeyboardButton("📥 Draw (အတုံးဆွဲရန်)", callback_data="draw_tile"),
            InlineKeyboardButton("⏭ Pass (အလှည့်ကျော်ရန်)", callback_data="pass_turn")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"📌 **ဘုတ်အစွန်းများ:** {board_str}\n\n"
        f"👤 ယခုအလှည့်: **{current_player_name}**\n"
        f"👇 အတုံးရွေးချယ်ရန် သို့မဟုတ် ဆွဲရန် အောက်ပါခလုတ်များကို နှိပ်ပါ!"
    )

    await context.bot.send_message(
        chat_id=game_session["chat_id"],
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    user_id = query.from_user.id

    if not game_session["active"] or user_id not in game_session["hands"]:
        await query.answer([], cache_time=0)
        return

    current_idx = game_session["current_turn"]
    if game_session["player_order"][current_idx] != user_id:
        results = [
            InlineQueryResultArticle(
                id="not_your_turn",
                title="⚠️ သင့်အလှည့် မဟုတ်သေးပါ!",
                input_message_content=InputTextMessageContent("⚠️ ယခု သင့်အလှည့် မဟုတ်သေးပါ။")
            )
        ]
        await query.answer(results, cache_time=0)
        return

    hand = game_session["hands"][user_id]
    results = []

    for idx, d in enumerate(hand):
        if d in game_session["sticker_mapping"]:
            sticker_id = game_session["sticker_mapping"][d]
            results.append(
                InlineQueryResultCachedSticker(
                    id=str(idx),
                    sticker_file_id=sticker_id,
                    input_message_content=InputTextMessageContent(f"PLAY_{user_id}_{idx}")
                )
            )
        else:
            results.append(
                InlineQueryResultArticle(
                    id=str(idx),
                    title=f"Domino [{d[0]}|{d[1]}]",
                    description="ဤအတုံးကို ချရန် နှိပ်ပါ",
                    input_message_content=InputTextMessageContent(f"PLAY_{user_id}_{idx}")
                )
            )

    await query.answer(results, cache_time=0)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not game_session["active"]:
        return

    user_id = query.from_user.id
    current_idx = game_session["current_turn"]

    if game_session["player_order"][current_idx] != user_id:
        await query.edit_message_text("⚠️ ဤသူ့အလှည့် မဟုတ်သေးပါ။")
        return

    action = query.data
    current_player_name = game_session["players"][user_id]

    if action == "draw_tile":
        if len(game_session["stockpile"]) > 0:
            new_tile = game_session["stockpile"].pop()
            game_session["hands"][user_id].append(new_tile)
            await context.bot.send_message(
                chat_id=game_session["chat_id"],
                text=f"📥 **{current_player_name}** သည် အတုံးတစ်တုံး ထပ်ဆွဲလိုက်ပါသည်။",
                parse_mode="Markdown"
            )
            await send_turn_message(context)
        else:
            await context.bot.send_message(
                chat_id=game_session["chat_id"],
                text=f"⚠️ ဆွဲစရာ အတုံး မကျန်တော့ပါ။ အလှည့်ကျော်ရန် Pass ကိုနှိပ်ပါ။"
            )

    elif action == "pass_turn":
        await context.bot.send_message(
            chat_id=game_session["chat_id"],
            text=f"⏭ **{current_player_name}** သည် အလှည့်ကို ကျော်လိုက်ပါသည်။",
            parse_mode="Markdown"
        )
        game_session["current_turn"] = (current_idx + 1) % len(game_session["player_order"])
        await send_turn_message(context)

async def handle_played_domino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not game_session["active"]:
        return

    text = update.message.text
    if not text or not text.startswith("PLAY_"):
        return

    try:
        parts = text.split("_")
        user_id = int(parts[1])
        idx = int(parts[2])
    except Exception:
        return

    current_idx = game_session["current_turn"]
    if game_session["player_order"][current_idx] != user_id:
        await update.message.reply_text("⚠️ ဤသူ့အလှည့် မဟုတ်သေးပါ!")
        return

    hand = game_session["hands"][user_id]
    if idx >= len(hand):
        return

    chosen_piece = hand[idx]
    board = game_session["board"]

    if not board:
        board.append(chosen_piece)
        hand.pop(idx)
    else:
        left_end = board[0][0]
        right_end = board[-1][1]

        if chosen_piece[0] == left_end:
            board.insert(0, (chosen_piece[1], chosen_piece[0]))
            hand.pop(idx)
        elif chosen_piece[1] == left_end:
            board.insert(0, chosen_piece)
            hand.pop(idx)
        elif chosen_piece[0] == right_end:
            board.append(chosen_piece)
            hand.pop(idx)
        elif chosen_piece[1] == right_end:
            board.append((chosen_piece[1], chosen_piece[0]))
            hand.pop(idx)
        else:
            await update.message.reply_text(f"❌ ဤအတုံးသည် ဘုတ်အစွန်းများနှင့် မကိုက်ညီပါ။ အခြားတုံးရွေးပါ (သို့မဟုတ် Draw/Pass ကိုသုံးပါ)။")
            return

    player_name = game_session["players"][user_id]
    await update.message.reply_text(f"🎴 {player_name} ချလိုက်သော အတုံး:")

    if chosen_piece in game_session["sticker_mapping"]:
        await context.bot.send_sticker(
            chat_id=game_session["chat_id"],
            sticker=game_session["sticker_mapping"][chosen_piece]
        )
    else:
        await update.message.reply_text(f"[{chosen_piece[0]}|{chosen_piece[1]}]")

    if len(hand) == 0:
        await update.message.reply_text(f"🎉 ဂိမ်းပြီးဆုံးပါပြီ! **{player_name}** က အနိုင်ရသွားပါပြီ။ 🏆", parse_mode="Markdown")
        game_session["active"] = False
        return

    game_session["current_turn"] = (current_idx + 1) % len(game_session["player_order"])
    await send_turn_message(context)

if __name__ == '__main__':
    token = "8803637837:AAFtInGXvW6wUiteoWrvsizj22oshIPTVoQ"

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgame", new_game))
    app.add_handler(CommandHandler("join", join_game))
    app.add_handler(CommandHandler("startgame", start_game))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_played_domino))

    print("Bot အလုပ်လုပ်နေပါပြီ ခင်ဗျာ...")
    app.run_polling()
