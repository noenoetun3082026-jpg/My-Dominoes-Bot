import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ဂိမ်းအချက်အလက်များကို သိမ်းဆည်းရန် ယာယီ Dictionary များ
game_session = {
    "active": False,
    "players": {},       # user_id: first_name
    "player_order": [],  # turn စီရန် user_id စာရင်း
    "hands": {},         # user_id: [dominoes]
    "board": [],         # ဘုတ်ပေါ်ရှိ အတုံးများ
    "current_turn": 0    # လက်ရှိကစားရမည့်သူ index
}

def create_dominoes():
    dominoes = []
    for i in range(7):
        for j in range(i, 7):
            dominoes.append((i, j))
    return dominoes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"မင်္ဂလာပါ {user_name} ရေ! Dominoes Bot မှ ကြိုဆိုပါတယ်။ 🎮\n\n"
        "ဂိမ်းစဖို့အတွက် /newgame လို့ ရိုက်ပါ။"
    )

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if game_session["active"]:
        await update.message.reply_text("⚠️ ဂိမ်းတစ်ခု လက်ရှိစတင်နေပါပြီ။ /join ဖြင့် ဝင်ရောက်နိုင်ပါတယ်။")
        return

    game_session["active"] = True
    game_session["players"] = {}
    game_session["player_order"] = []
    game_session["hands"] = {}
    game_session["board"] = []
    game_session["current_turn"] = 0

    await update.message.reply_text(
        "🎲 Dominoes ဂိမ်းအခန်း (Game Room) စတင်လိုက်ပါပြီ!\n"
        "ကစားချင်သူများက /join လို့ ရိုက်ပြီး ဝင်ရောက်နိုင်ပါတယ်။\n"
        "အားလုံးဝင်ပြီးရင် /startgame လို့ ရိုက်ပြီး ဂိမ်းစတင်နိုင်ပါတယ်။"
    )

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not game_session["active"]:
        await update.message.reply_text("❌ လက်ရှိ ဖွင့်ထားသော ဂိမ်းအခန်းမရှိသေးပါ။ /newgame ဖြင့် အစပျိုးပါ။")
        return

    user = update.effective_user
    if user.id in game_session["players"]:
        await update.message.reply_text(f"{user.first_name}, သင် ဝင်ထားပြီးသား ဖြစ်ပါတယ်။")
        return

    game_session["players"][user.id] = user.first_name
    game_session["player_order"].append(user.id)
    await update.message.reply_text(f"✅ {user.first_name} ဂိမ်းထဲသို့ ဝင်ရောက်လာပါပြီ! (စုစုပေါင်း ကစားသမား: {len(game_session['players'])} ဦး)")

async def send_hand_to_player(context, user_id):
    player_name = game_session["players"][user_id]
    hand = game_session["hands"][user_id]
    
    # ခလုတ်များ ဖန်တီးရန် (တစ်တုံးချင်းစီကို Button လုပ်မည်)
    keyboard = []
    for idx, d in enumerate(hand):
        keyboard.append([InlineKeyboardButton(f"[{d[0]}|{d[1]}]", callback_data=f"play_{idx}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    board_str = " (ဗလာ - ပထမဆုံးချပါ)" if not game_session["board"] else f"[{game_session['board'][0][0]}|...] မှ [...|{game_session['board'][-1][1]}] အထိ"
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎴 သင့်လက်ထဲရှိ အတုံးများ:\nဘုတ်အစွန်းများ: {board_str}\nအောက်ပါအတုံးများထဲမှ တစ်တုံးကို ရွေးချယ်ပါ -",
            reply_markup=reply_markup
        )
    except Exception:
        pass

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
        player_hand = [dominoes.pop() for _ in range(7)]
        game_session["hands"][player_id] = player_hand

    first_player_id = game_session["player_order"][0]
    first_player_name = game_session["players"][first_player_id]

    await update.message.reply_text(
        f"🎮 ဂိမ်းစတင်ပါပြီ!\n"
        f"ပထမဆုံး ကစားရမည့်သူ: **{first_player_name}**\n"
        f"ကစားသမားများ၏ Private Chat သို့ အတုံးများ ပို့လိုက်ပါပြီ။"
    )

    # အားလုံးကို လက်ထဲက အတုံးတွေ ပို့ပေးမည် (ပထမလူကို အလှည့်ပေးမည်)
    for player_id in game_session["player_order"]:
        await send_hand_to_player(context, player_id)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if not game_session["active"]:
        await query.edit_message_text(text="❌ လက်ရှိ ဂိမ်းမရှိတော့ပါ။")
        return

    # အလှည့် စစ်ဆေးခြင်း
    current_idx = game_session["current_turn"]
    if game_session["player_order"][current_idx] != user_id:
        await query.answer("⚠️ ယခု မည်သူ့အလှည့်မှ မဟုတ်သေးပါ (သို့မဟုတ်) သင့်အလှည့် မရောက်သေးပါ။", show_alert=True)
        return

    data = query.data
    if data.startswith("play_"):
        idx = int(data.split("_")[1])
        hand = game_session["hands"][user_id]
        
        if idx >= len(hand):
            await query.answer("⚠️ ဒီအတုံး မရှိတော့ပါ။", show_alert=True)
            return

        chosen_piece = hand[idx]
        board = game_session["board"]

        # ဘုတ်ပေါ်တွင် အတုံးချခြင်း စည်းမျဉ်း
        if not board:
            # ပထမဆုံး အတုံး
            board.append(chosen_piece)
            hand.pop(idx)
        else:
            left_end = board[0][0]
            right_end = board[-1][1]

            if chosen_piece[0] == left_end:
                # ဘယ်ဘက်သို့ ဆက်ရန် (လှန်ထည့်မည်)
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
                await query.answer("❌ ဤအတုံးကို လက်ရှိ ဘုတ်အစွန်းများနှင့် ဆက်၍ မရပါ။", show_alert=True)
                return

        # အနိုင်အရှုံး စစ်ဆေးခြင်း
        if len(hand) == 0:
            winner_name = game_session["players"][user_id]
            await query.edit_message_text(text=f"🎉 ဂိမ်းပြီးဆုံးပါပြီ! **{winner_name}** က အနိုင်ရသွားပါပြီ။ 🏆")
            game_session["active"] = False
            return

        # နောက်တစ်ယောက်သို့ အလှည့်ပြောင်းခြင်း
        game_session["current_turn"] = (current_idx + 1) % len(game_session["player_order"])
        next_player_id = game_session["player_order"][game_session["current_turn"]]
        next_player_name = game_session["players"][next_player_id]

        board_str = ", ".join([f"[{d[0]}|{d[1]}]" for d in board])
        await query.edit_message_text(text=f"✅ တုံးချပြီးပါပြီ!\nလက်ရှိဘုတ်: {board_str}\n\nလက်ကျန်အတုံးများကို ဆက်လက်ကစားပါ။")

        # အားလုံးကို လက်ရှိဘုတ်အခြေအနေနဲ့ ဘယ်သူ့အလှည့်လဲ အသိပေးခြင်း
        for pid in game_session["player_order"]:
            if pid != user_id:
                try:
                    await context.bot.send_message(
                        chat_id=pid,
                        text=f"📢 ကစားသမား {game_session['players'][user_id]} က [{chosen_piece[0]}|{chosen_piece[1]}] ကို ချလိုက်ပါပြီ။\nလက်ရှိဘုတ်: {board_str}\n\nယခုအလှည့်: **{next_player_name}**"
                    )
                except Exception:
                    pass
            else:
                # ကိုယ့်လက်ကျန်အတုံးများကို update လုပ်ပေးရန်
                await send_hand_to_player(context, pid)

if __name__ == '__main__':
    token = "8803637837:AAFtInGXvW6wUiteoWrvsizj22oshIPTVoQ"

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgame", new_game))
    app.add_handler(CommandHandler("join", join_game))
    app.add_handler(CommandHandler("startgame", start_game))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot အလုပ်လုပ်နေပါပြီ ခင်ဗျာ...")
    app.run_polling()
