"""
緯穎(6669) 飆股核心持有 監控
------------------------------------------------------------
原則:只有「你真金白銀的部位」需要盯(成本/股數,有交易才改);其餘市價/季高/RSI全部
     當下從 yfinance 歷史資料算,不寫死。另有一筆核心持股在別的券商,不列入這裡管理。
策略:核心抱著看它跑;過熱貼前高才考慮賣強鎖利一部分,別追高、別往下大攤(波動極大、留子彈)。
提醒:若除權息真的執行(1張變3張),yfinance歷史會被打亂、此檔需再特殊處理;股價跳到約1/3是換算非崩盤。
成本/股數:見 app 內持倉管理(不寫死於程式碼)。
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "6669.TW"
NAME = "緯穎"

# ====== 你的部位(真金白銀,app 內持倉管理可改) ======
COST, SHARES = positions_store.get_lot(SYMBOL)
# ============================================

def get_data():
    """市價 + 近一季高 + RSI14 + 成交量,全部從資料算(不寫死)。"""
    tk = yf.Ticker(SYMBOL)
    price = None
    try:
        info = tk.info
        price = info.get('regularMarketPrice') or info.get('currentPrice')
    except Exception:
        pass
    hi = rsi = vol = vol_ma20 = None
    try:
        df = tk.history(period="3mo", auto_adjust=False)
        h = df['Close'].dropna()
        if price is None and len(h):
            price = float(h.iloc[-1])
        if len(h):
            hi = float(h.max())                 # 近一季高(資料算)
        if len(h) >= 15:                        # RSI14(資料算)
            diff = h.diff().dropna()
            up = diff.clip(lower=0).rolling(14).mean().iloc[-1]
            dn = (-diff.clip(upper=0)).rolling(14).mean().iloc[-1]
            rsi = 100.0 if dn == 0 else 100 - 100 / (1 + up / dn)
        if len(df) >= 20:
            vol = float(df['Volume'].iloc[-1])
            vol_ma20 = float(df['Volume'].rolling(20).mean().iloc[-1])
    except Exception:
        pass
    return (float(price) if price else None,
            round(hi) if hi else None,
            round(rsi) if rsi is not None else None,
            vol, vol_ma20)

def vol_desc(vol, vol_ma20):
    if not vol or not vol_ma20:
        return "抓不到"
    ratio = vol / vol_ma20
    tag = "放量" if ratio >= 1.5 else ("量縮" if ratio <= 0.5 else "量平")
    return f"{tag}(今日{vol:,.0f}股，是20日均量的{ratio*100:.0f}%)"

def judge(price, hi, rsi, vol=None, vol_ma20=None):
    overheat = (hi and price >= hi * 0.99) or (rsi and rsi >= 75)
    if overheat:
        tag = []
        if rsi: tag.append(f"RSI {rsi}")
        if hi:  tag.append(f"近季高 {hi}")
        return (f"🔴 {price} 過熱貼高({'、'.join(tag)}) — 核心抱、別追高加碼;"
                f"想鎖利只賣一部分,別把飆股賣光。")
    return (f"⚪ {price} 核心抱著看它跑(大贏家已到手) — 沒事不用動,"
            f"別追高、回檔別往下大攤(波動極大、留子彈)。")

def run():
    price, hi, rsi, vol, vol_ma20 = get_data()
    print(f"=== {NAME}({SYMBOL}) 飆股核心持有 ===")
    if price is None:
        print("市價：抓取失敗(yfinance 資料異常)。請以券商App實際市價為準。")
        return
    extra = []
    if rsi is not None: extra.append(f"RSI：{rsi}")
    if hi is not None:  extra.append(f"近季高：{hi}")
    line2 = ("    " + "    ".join(extra)) if extra else ""
    if SHARES:
        pnl = (price / COST - 1) * 100
        print(f"市價：{price}    均價：{COST}（帳面 {pnl:+.0f}%）    {SHARES} 股{line2}")
    else:
        print(f"市價：{price}    空手{line2}")
    print(f"成交量：{vol_desc(vol, vol_ma20)}")
    print(judge(price, hi, rsi))
    print(f"\n備忘：核心抱、贏家已到手 / 市價·季高·RSI全從資料算(不寫死) / "
          f"只有成本股數寫在持倉管理裡,有交易才改 / 若除權息股數變3倍別嚇到(需再特殊處理)")

if __name__ == "__main__":
    run()
