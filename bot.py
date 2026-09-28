import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# /start လို့ ရိုက်လိုက်ရင် တုံ့ပြန်မယ့် ပရိုဂရမ်
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"မင်္ဂလာပါ {user_name} ရေ! Dominoes Bot မှ ကြိုဆိုပါတယ်။ 🎮\n\n"
        "ဂိမ်းစဖို့အတွက် /newgame လို့ ရိုက်ပါ။"
    )

# /newgame လို့ ရိုက်လိုက်ရင် ဂိမ်းအခန်းစမယ့် ပရိုဂရမ်
async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲 Dominoes ဂိမ်းအခန်း (Game Room) စတင်လိုက်ပါပြီ!\n"
        "ကစားချင်သူများက /join လို့ ရိုက်ပြီး ဝင်ရောက်နိုင်ပါတယ်။"
    )

if __name__ == '__main__':
    # သင့်ရဲ့ Bot Token ကို တိုက်ရိုက်ထည့်ပေးထားပါတယ်
    token = "8803637837:AAFtInGXvW6wUiteoWrvsizj22oshIPTVoQ"

    app = ApplicationBuilder().token(token).build()

    # Command တွေကို ချိတ်ဆက်ခြင်း
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgame", new_game))

    print("Bot အလုပ်လုပ်နေပါပြီ ခင်ဗျာ...")
    app.run_polling()
