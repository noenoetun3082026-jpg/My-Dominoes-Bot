import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ဂိမ်းအချက်အလက်များကို သိမ်းဆည်းရန် ယာယီ Dictionary များ
game_session = {
    "active": False,
    "players": [],
    "hands": {}
}

# Dominoes အတုံး ၂၈ တုံး ဖန်တီးရန်
def create_dominoes():
    dominoes = []
    for i in range(7):
        for j in range(i, 7):
            dominoes.append((i, j))
    return dominoes

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"မင်္ဂလာပါ {user_name} ရေ! Dominoes Bot မှ ကြိုဆိုပါတယ်။ 🎮\n\n"
        "ဂိမ်းစဖို့အတွက် /newgame လို့ ရိုက်ပါ။"
    )

# /newgame - ဂိမ်းအခန်းစရန်
async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if game_session["active"]:
        await update.message.reply_text("⚠️ ဂိမ်းတစ်ခု လက်ရှိစတင်နေပါပြီ။ /join ဖြင့် ဝင်ရောက်နိုင်ပါတယ်။")
        return

    game_session["active"] = True
    game_session["players"] = []
    game_session["hands"] = {}

    await update.message.reply_text(
        "🎲 Dominoes ဂိမ်းအခန်း (Game Room) စတင်လိုက်ပါပြီ!\n"
        "ကစားချင်သူများက /join လို့ ရိုက်ပြီး ဝင်ရောက်နိုင်ပါတယ်။\n"
        "အားလုံးဝင်ပြီးရင် Host မှ /startgame လို့ ရိုက်ပြီး ဂိမ်းစတင်နိုင်ပါတယ်။"
    )

# /join - ကစားသမားအဖြစ် ဝင်ရောက်ရန်
async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not game_session["active"]:
        await update.message.reply_text("❌ လက်ရှိ ဖွင့်ထားသော ဂိမ်းအခန်းမရှိသေးပါ။ /newgame ဖြင့် အစပျိုးပါ။")
        return

    user = update.effective_user
    if user.id in game_session["players"]:
        await update.message.reply_text(f"{user.first_name}, 您 သင် ဝင်ထားပြီးသား ဖြစ်ပါတယ်။")
        return

    game_session["players"].append(user.id)
    await update.message.reply_text(f"✅ {user.first_name} ဂိမ်းထဲသို့ ဝင်ရောက်လာပါပြီ! (စုစုပေါင်း ကစားသမား: {len(game_session['players'])} ဦး)")

# /startgame - ဂိမ်းစတင်ပြီး အတုံးများ ဝေပေးရန်
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not game_session["active"]:
        await update.message.reply_text("❌ ဂိမ်းမစရသေးပါ။")
        return

    if len(game_session["players"]) < 1:
        await update.message.reply_text("⚠️ ကစားသမား အနည်းဆုံး ၁ ဦး လိုအပ်ပါသည်။")
        return

    # အတုံးများ ဖန်တီးပြီး ရောနှောခြင်း
    dominoes = create_dominoes()
    random.shuffle(dominoes)

    # ကစားသမားတစ်ဦးလျှင် အတုံး ၇ တုံးစီ ဝေပေးခြင်း
    text = "🎮 ဂိမ်းစတင်ပါပြီ!\n\nကစားသမားများ၏ လက်ထဲပါလာသော အတုံးများ:\n"
    for player_id in game_session["players"]:
        player_hand = [dominoes.pop() for _ in range(7)]
        game_session["hands"][player_id] = player_hand
        
        # Chat ထဲသို့ တိုက်ရိုက် ထုတ်ပြပေးခြင်း (Telegram တွင် Private message ပို့ရန်လည်း ပြင်ဆင်နိုင်သည်)
        text += (f"👤 User ID {player_id}: " + ", ".join([f"[{d[0]}|{d[1]}]" for d in player_hand]) + "\n")

    await update.message.reply_text(text)

if __name__ == '__main__':
    token = "8803637837:AAFtInGXvW6wUiteoWrvsizj22oshIPTVoQ"

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgame", new_game))
    app.add_handler(CommandHandler("join", join_game))
    app.add_handler(CommandHandler("startgame", start_game))

    print("Bot အလုပ်လုပ်နေပါပြီ ခင်ဗျာ...")
    app.run_polling()
