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
                {"text": f"⏳ {sym} GTT SCHEDULED", "callback_data": f"confirm_sched_EQ_{sym}_{price}_{sl}_{t2}_{qty}"},
                {"text": f"🟢 {sym} EXECUTED", "callback_data": f"confirm_exec_EQ_{sym}_{price}_{sl}_{t2}_{qty}"},
                {"text": f"❌ SKIP", "callback_data": f"confirm_skipped_{sym}"}
            ])
        sections.append("\n\n".join(eq_text))

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
                {"text": f"⏳ {name} GTT SCHEDULED (3 Lots)", "callback_data": f"confirm_sched_CMD_{name}_{entry}_{sl}_{t2}_3_{margin*3}"},
                {"text": f"🟢 {name} EXECUTED (3 Lots)", "callback_data": f"confirm_exec_CMD_{name}_{entry}_{sl}_{t2}_3_{margin*3}"},
                {"text": f"❌ SKIP", "callback_data": f"confirm_skipped_{name}"}
            ])
        sections.append("\n\n".join(cmd_text))

    if not sections:
        return True

    message = (
        "\n\n".join(sections) +
        f"\n\n👉 *Open Upstox App -> Place Orders -> Tap '⏳ GTT SCHEDULED' or '🟢 EXECUTED'!*"
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
        return res.status_code == 200
    except Exception as e:
        print(f"Failed to send combined trade cards: {e}")
        return False
