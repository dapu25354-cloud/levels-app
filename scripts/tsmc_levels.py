"""
台積電(2330) 核心抱著衝 + 機動倉高賣低撿 關卡監控
------------------------------------------------------------
背景:權值龍頭、健康大多頭,核心奉行「順勢抱,別來回做」。
部位:核心(長線不動) + 機動倉(多買來要賣的)。
策略:核心不管盤整回檔都不動,只有跌破季線才重評;機動倉單獨判斷,過熱/貼近前高就賣鎖利,
     拉回月線可考慮買回。別把機動倉的操作動作套用到核心上——核心是抱著讓它衝,機動倉才是操作的。
成本/股數(核心/機動兩組):見 app 內持倉管理(不寫死於程式碼)。

關卡(均線即時算):
  機動倉:RSI≥75 或 貼近近60日高(*0.985)  = 賣機動倉鎖利,核心不動
  機動倉:拉回月線(20MA)附近              = 若已賣掉,可考慮買回機動倉
  核心:跌破月線(20MA)                    = 回檔,通常是機會,核心不動,守季線
  核心:跌破季線(60MA)                    = 龍頭轉弱(罕見),核心才需要認真重評
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "2330.TW"
NAME = "台積電"
CORE_COST, CORE_SHARES = positions_store.get_lot(SYMBOL, "core")
TACTICAL_COST, TACTICAL_SHARES = positions_store.get_lot(SYMBOL, "tactical")

def rsi(close, window=14):
    delta = close.diff()
    up = delta.clip(lower=0).rolling(window).mean()
    down = -delta.clip(upper=0).rolling(window).mean()
    rs = up / down
    return 100 - (100 / (1 + rs))

def get_data():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="6mo", auto_adjust=False)
    c = df['Close']
    price = float(c.iloc[-1])
    ma20 = float(c.rolling(20).mean().iloc[-1])
    ma60 = float(c.rolling(60).mean().iloc[-1])
    high60 = float(c.iloc[-60:].max())
    rs14 = float(rsi(c).iloc[-1])
    vol = float(df['Volume'].iloc[-1])
    vol_ma20 = float(df['Volume'].rolling(20).mean().iloc[-1])
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            price = float(rp)
    except Exception:
        pass
    return price, ma20, ma60, high60, rs14, vol, vol_ma20

def vol_desc(vol, vol_ma20):
    ratio = vol / vol_ma20 if vol_ma20 else 1.0
    tag = "放量" if ratio >= 1.5 else ("量縮" if ratio <= 0.5 else "量平")
    return f"{tag}(今日{vol:,.0f}股，是20日均量的{ratio*100:.0f}%)", ratio

TOL = 0.01

def judge_core(price, ma20, ma60):
    if price < ma60 * (1 - TOL):
        return f"⚠️ 跌破季線({ma60:.0f}) — 龍頭轉弱(罕見),核心才需要認真重評。"
    if price < ma20 * (1 - TOL):
        return f"🟡 回檔到月線({ma20:.0f})下 — 大牛股回檔常是機會,核心不動,守季線({ma60:.0f})。"
    return f"⚪ 健康多頭(月線{ma20:.0f}上) — 核心抱著讓它衝,不用盯。"

def judge_tactical(price, ma20, high60, rs14):
    if not TACTICAL_SHARES:
        return "⚪ 機動倉目前空手,等拉回月線再考慮接回。"
    if rs14 >= 75:
        return f"🔴 RSI過熱({rs14:.0f}) — 機動倉{TACTICAL_SHARES}股可考慮賣出鎖利(成本{TACTICAL_COST}),核心{CORE_SHARES}股不動。"
    if price >= high60 * 0.985:
        return f"🔴 貼近近60日高點({high60:.0f}) — 機動倉{TACTICAL_SHARES}股可考慮賣出鎖利(成本{TACTICAL_COST}),核心{CORE_SHARES}股不動。"
    if price <= ma20 * 1.02:
        return f"🟢 拉回月線({ma20:.0f})附近 — 若機動倉已賣掉,這是考慮買回的點。"
    return "⚪ 機動倉續抱,等貼近前高或RSI過熱再賣、或等拉回月線再買回。"

def run():
    price, ma20, ma60, high60, rs14, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) 核心抱著衝 + 機動倉高賣低撿 ===")
    print(f"市價：{price}    月線：{ma20:.0f}    季線：{ma60:.0f}    近60日高：{high60:.0f}    RSI：{rs14:.0f}")
    print(f"成交量：{vdesc}")
    parts = []
    if CORE_SHARES:
        core_pnl = (price / CORE_COST - 1) * 100
        parts.append(f"核心{CORE_SHARES}股(成本約{CORE_COST},帳面約{core_pnl:+.0f}%)不動")
    if TACTICAL_SHARES:
        tac_pnl = (price / TACTICAL_COST - 1) * 100
        parts.append(f"機動{TACTICAL_SHARES}股(成本{TACTICAL_COST},帳面{tac_pnl:+.0f}%)可操作")
    print("部位：" + (" + ".join(parts) if parts else "空手"))
    print("【核心】" + judge_core(price, ma20, ma60))
    print("【機動】" + judge_tactical(price, ma20, high60, rs14))
    print("\n備忘：核心沒事不動、跌破季線才重評 / 機動過熱或貼近前高就賣鎖利、拉回月線可買回")

if __name__ == "__main__":
    run()
