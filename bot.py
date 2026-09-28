import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, CommandHandler, InlineQueryHandler, ContextTypes

game_session = {
    "active": False,
    "players": {},
    "player_order": [],
    "hands": {},
    "board": [],
    "current_turn": 0,
    "chat_id": None
}

def create_dominoes():
    dominoes = []
    for i in range(7):
        for j in range(i, 7):
            dominoes.append((i, j))
    return dominoes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("မင်္ဂလာပါ! Dominoes Bot မှ ကြိုဆိုပါတယ်။ ဂိမ်းစဖို့ /newgame လို့ ရိုက်ပါ။")

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if game_session["active"]:
        await update.message.reply_text("⚠️ ဂိမ်းတစ်ခု လက်ရှိစတင်နေပါပြီ။ /join ဖြင့် ဝင်ရောက်ပါ။")
        return

    game_session["active"] = True
    game_session["players"] = {}
    game_session["player_order"] = []
    game_session["hands"] = {}
    game_session["board"] = []
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

    dominoes = create_dominoes()
    random.shuffle(dominoes)

    game_session["board"] = []
    game_session["current_turn"] = 0

    for player_id in game_session["player_order"]:
        game_session["hands"][player_id] = [dominoes.pop() for _ in range(7)]

    await send_turn_message(context)

async def send_turn_message(context: ContextTypes.DEFAULT_TYPE):
    current_player_id = game_session["player_order"][game_session["current_turn"]]
    current_player_name = game_session["players"][current_player_id]

    keyboard = [
        [InlineKeyboardButton("Make your choice!", switch_inline_query_current_chat="")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"First player: **{current_player_name}**\n"
        f"ယခုအလှည့်ရောက်ပါပြီ။ အတုံးရွေးချယ်ရန် အောက်ပါခလုတ်ကို နှိပ်ပါ!"
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
        results.append(
            InlineQueryResultArticle(
                id=str(idx),
                title=f"Domino [{d[0]}|{d[1]}]",
                description="ဤအတုံးကို ချရန် နှိပ်ပါ",
                input_message_content=InputTextMessageContent(f"🎴 ချလိုက်သော အတုံး: [{d[0]}|{d[1]}]")
            )
        )

    await query.answer(results, cache_time=0)

if __name__ == '__main__':
    token = "8803637837:AAFtInGXvW6wUiteoWrvsizj22oshIPTVoQ"

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgame", new_game))
    app.add_handler(CommandHandler("join", join_game))
    app.add_handler(CommandHandler("startgame", start_game))
    app.add_handler(InlineQueryHandler(inline_query))

    print("Bot အလုပ်လုပ်နေပါပြီ ခင်ဗျာ...")
    app.run_polling()
