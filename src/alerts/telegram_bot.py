import requests
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_combined_clean_trade_cards(equity_signals: list, commodity_signals: list) -> bool:
    """
    Dispatches EXACTLY 1 COMBINED Telegram Message containing both Equity & Commodity cards.
    Displays Dual Targets (1.5R Scale-Out & 2.5R Final) and Multi-Timeframe Badges!
    """
    sections = []
    inline_buttons = []

    # 1. Equity Section
    if equity_signals:
        eq_text = ["====================================\n📈 **1. NSE EQUITY SWING TRADE CARDS**\n===================================="]
        for sig in equity_signals:
            sym = sig['symbol']
            price = sig['price']
            sl = sig['stop_loss']
            t1 = sig.get('target1', price + (abs(price - sl) * 1.5))
            t2 = sig['target']
            qty = sig['quantity']
            mtf_badge = sig.get('mtf_badge', '🟢 15M + 1H + 1D ALIGNED')
            
            eq_text.append(
                f"📌 **{sym}**  | Win Score: **{sig['quant_score']}/100**\n"
                f"   • {mtf_badge}\n"
                f"   • **BUY**: ₹{price:,.2f} | **SL**: ₹{sl:,.2f}\n"
                f"   • 🎯 **TARGET 1 (Scale 50% & SL to Cost)**: **₹{t1:,.2f}** (+1.5R)\n"
                f"   • 🎯 **TARGET 2 (Final Target)**: **₹{t2:,.2f}** (+2.5R)\n"
                f"   • **REC. QTY**: **{qty} Shares** (Max Risk: ₹{sig['risk_amount']:,.2f})"
            )
            inline_buttons.append([
                {"text": f"⏳ {sym} GTT SCHEDULED", "callback_data": f"cs_EQ_{sym}_{round(price,1)}_{round(sl,1)}_{round(t2,1)}_{qty}"},
                {"text": f"🟢 {sym} EXECUTED", "callback_data": f"ce_EQ_{sym}_{round(price,1)}_{round(sl,1)}_{round(t2,1)}_{qty}"},
                {"text": f"❌ SKIP", "callback_data": f"c_skip_{sym}"}
            ])
        sections.append("\n\n".join(eq_text))
    else:
        sections.append(
            "====================================\n"
            "📈 **1. NSE EQUITY SWING TRADE CARDS**\n"
            "====================================\n"
            "ℹ️ **Market Status**: No stocks met strict Quant Score (≥70.0) criteria today.\n"
            "🛡️ *Capital 100% Protected (0 risky trades taken).*"
        )

    # 2. Commodity Section
    if commodity_signals:
        cmd_text = ["====================================\n🥇 **2. MCX COMMODITY FUTURES CARDS** (15-DAY HOLDING)\n===================================="]
        for sig in commodity_signals:
            name = sig['mcx_ticker']
            exp = sig['expiry_month']
            entry = sig['mcx_entry_price']
            sl = sig['mcx_stop_loss']
            t1 = sig.get('target1', entry + (abs(entry - sl) * 1.5))
            t2 = sig['mcx_target']
            margin = sig['approx_margin']
            mtf_badge = sig.get('mtf_badge', '🟢 15M + 1H + 1D ALIGNED')
            
            cmd_text.append(
                f"🥇 **{name} {exp}**  | Win Score: **{sig['quant_score']}/100**\n"
                f"   • {mtf_badge}\n"
                f"   • **BUY FUTURES**: ₹{entry:,.2f} | **SL**: ₹{sl:,.2f}\n"
                f"   • 🎯 **TARGET 1 (Book 50% & SL to Breakeven)**: **₹{t1:,.2f}** (+1.5R)\n"
                f"   • 🎯 **TARGET 2 (Final Target)**: **₹{t2:,.2f}** (+2.5R)\n"
                f"   • **MARGIN REQ**: ₹{margin:,.2f} per lot (Capped under ₹20k)"
            )
            inline_buttons.append([
                {"text": f"⏳ {name} GTT SCHEDULED (3 Lots)", "callback_data": f"cs_CMD_{name}_{round(entry,1)}_{round(sl,1)}_{round(t2,1)}_3_{round(margin*3,1)}"},
                {"text": f"🟢 {name} EXECUTED (3 Lots)", "callback_data": f"ce_CMD_{name}_{round(entry,1)}_{round(sl,1)}_{round(t2,1)}_3_{round(margin*3,1)}"},
                {"text": f"❌ SKIP", "callback_data": f"c_skip_{name}"}
            ])
        sections.append("\n\n".join(cmd_text))
    else:
        sections.append(
            "====================================\n"
            "🥇 **2. MCX COMMODITY FUTURES CARDS**\n"
            "====================================\n"
            "ℹ️ **Commodity Status**: MCX contracts currently consolidating (Quant Scores < 70.0).\n"
            "🛡️ *Capital 100% Protected (0 risky trades taken).*"
        )

    message = (
        "\n\n".join(sections) +
        "\n\n👉 Open Upstox App -> Place Orders -> Tap '⏳ GTT SCHEDULED' or '🟢 EXECUTED'!"
    )

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n" + "="*50)
        print(message)
        print("="*50 + "\n")
        return True

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": {"inline_keyboard": inline_buttons}
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("✅ Combined Equity & Commodity Trade Cards sent to Telegram!")
            return True
        else:
            print(f"⚠️ Telegram Markdown Error ({res.status_code}): {res.text}. Retrying with plain text...")
            payload_plain = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "reply_markup": {"inline_keyboard": inline_buttons}
            }
            res_plain = requests.post(url, json=payload_plain, timeout=10)
            if res_plain.status_code == 200:
                print("✅ Combined Trade Cards delivered via Plain Text fallback!")
                return True
            else:
                print(f"❌ Failed to send combined trade cards: {res_plain.text}")
                return False
    except Exception as e:
        print(f"Failed to send combined trade cards: {e}")
        return False
