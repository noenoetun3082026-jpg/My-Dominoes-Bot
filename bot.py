from telegram import InlineQueryResultCachedSticker

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
        # တုံးနှင့်သက်ဆိုင်သော sticker file_id ရှိမရှိ စစ်ဆေးခြင်း
        if d in game_session["sticker_mapping"]:
            sticker_id = game_session["sticker_mapping"][d]
            # Inline Menu ထဲတွင် စတစ်ကာပုံစံ ပေါ်စေရန် CachedSticker ကိုသုံးခြင်း
            results.append(
                InlineQueryResultCachedSticker(
                    id=str(idx),
                    sticker_file_id=sticker_id,
                    input_message_content=InputTextMessageContent(f"PLAY_{user_id}_{idx}")
                )
            )
        else:
            # စတစ်ကာမရှိလျှင် ယခင်အတိုင်း စာသားဖြင့် ပြမည်
            results.append(
                InlineQueryResultArticle(
                    id=str(idx),
                    title=f"Domino [{d[0]}|{d[1]}]",
                    description="ဤအတုံးကို ချရန် နှိပ်ပါ",
                    input_message_content=InputTextMessageContent(f"PLAY_{user_id}_{idx}")
                )
            )

    await query.answer(results, cache_time=0)
