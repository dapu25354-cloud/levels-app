"""
國票金(2889) 監控 — 兩塊分開看
------------------------------------------------------------
底倉:長期定存/領息股,不是波段持股。看的是殖利率與成本,不是短期動能/RSI。
     (它在金融組裡動能最弱、季報酬常負,但對老股「不公平」用波段尺評,別被嚇到。)
     策略:放著領息,短期紅綠不理。只有「基本面/配息變壞」或「跌很深」才需要看一眼確認,否則續抱。
     這筆底倉不在這套系統追蹤的帳戶裡,不列成本/股數。

加碼倉(波段倉):題材帶動時另外加碼的部位,要照鎖利邏輯盯(不是定存股邏輯)。
     鎖利線 = 進場後最高收盤價 x (1-SWING_GIVEBACK)，且不會低於成本 —— 只會往上墊高、不會因為連續小跌
     就跟著滑下去(舊版用「近5日低點」有這個漏洞，已改掉)。
成本/股數/進場日期:見 app 內持倉管理(不寫死於程式碼)。
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "2889.TW"
NAME = "國票金"

SWING_COST, SWING_SHARES = positions_store.get_lot(SYMBOL, "swing")
_swing = positions_store.get_lot_full(SYMBOL, "swing")
SWING_ENTRY_DATE = _swing.get("entry_date")  # 進場約略時間點(這波起漲前)
SWING_GIVEBACK = 0.03  # 鎖利線 = 進場後最高收盤 x (1-3%)（策略性固定比例,非個人金額）

def get_data():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="6mo", auto_adjust=False)
    c = df['Close']
    price = float(c.iloc[-1])
    ma60 = float(c.rolling(60).mean().iloc[-1])
    high120 = float(c.max())
    vol = float(df['Volume'].iloc[-1])
    vol_ma20 = float(df['Volume'].rolling(20).mean().iloc[-1])
    if SWING_ENTRY_DATE:
        since_entry = c[c.index.tz_localize(None) >= SWING_ENTRY_DATE]
        high_since_entry = float(since_entry.max()) if len(since_entry) else price
    else:
        high_since_entry = price
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            price = float(rp)
            high_since_entry = max(high_since_entry, price)
    except Exception:
        pass
    return price, ma60, high120, vol, vol_ma20, high_since_entry

def vol_desc(vol, vol_ma20):
    ratio = vol / vol_ma20 if vol_ma20 else 1.0
    tag = "放量" if ratio >= 1.5 else ("量縮" if ratio <= 0.5 else "量平")
    return f"{tag}(今日{vol:,.0f}股，是20日均量的{ratio*100:.0f}%)", ratio

def judge(price, ma60, high120, vol=None, vol_ma20=None):
    if price < ma60 * 0.9:
        return (f"🟡 {price} 比近期高檔({high120:.1f})/季線回得較深 — 確認一下獲利/配息有沒有變壞,"
                f"沒變就續抱領息,別用波段恐慌砍長線定存股。")
    return (f"⚪ {price} 長線定存/領息股 — 放著領息,看殖利率與成本、不看短期動能。短期紅綠不理。")

def swing_judge(price, high_since_entry):
    if not SWING_SHARES:
        return "波段倉：目前空手。", "⚪ 沒部位,等題材/訊號出現再考慮進場。"
    pnl = (price / SWING_COST - 1) * 100
    stop = max(SWING_COST, high_since_entry * (1 - SWING_GIVEBACK))
    line = (f"波段倉：成本{SWING_COST}·{SWING_SHARES}股   市價{price}（帳面{pnl:+.1f}%）   "
            f"進場後最高{high_since_entry:.2f}   鎖利線：{stop:.2f}")
    if price <= stop:
        action = f"🔴 已跌破鎖利線{stop:.2f} — 出場,把獲利收進口袋。"
    else:
        action = f"🟢 在鎖利線{stop:.2f}之上 — 續抱。這條線只會往上墊高,不會跌回成本價,破了才要跑。"
    return line, action

def run():
    price, ma60, high120, vol, vol_ma20, high_since_entry = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) ===")
    print(f"市價：{price}    季線：{ma60:.1f}（僅參考）    成交量：{vdesc}")
    print()
    print("【底倉-定存領息,不管】")
    print(judge(price, ma60, high120))
    print()
    print("【波段加碼倉-鎖利盯】")
    line, action = swing_judge(price, high_since_entry)
    print(line)
    print(action)
    print(f"\n備忘：底倉放著領息不理短線 / 加碼倉鎖利線只會往上墊高,絕不會滑回成本價")

if __name__ == "__main__":
    run()
