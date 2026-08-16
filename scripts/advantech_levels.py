"""
研華(2395) 健康多頭/順勢抱 關卡監控
------------------------------------------------------------
背景:工業電腦龍頭、健康多頭、貼近季高。穩、不暴衝。
     現有持股定調為【核心】不賣(忍過長時間悶盤才等到噴出);之後若再加碼,是機動倉,
     想辦法抱住增加持股,別像核心之前一樣被洗來洗去。
策略:核心不賣、順勢抱;拉回20MA可小撿(機動);真過熱才賣強(機動);跌破60MA才留意。同世禾/順達邏輯。
成本/股數:見 app 內持倉管理(不寫死於程式碼)。

關卡(均線即時算):
  過熱貼高(RSI≥70+近季高) = 可賣強鎖利
  創高           = 沒過熱續抱
  20MA上未過熱   = 健康多頭,順勢抱
  跌破20MA       = 回檔,守60日線、可小撿
  跌破60MA       = 轉弱,留意減碼
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "2395.TW"
NAME = "研華"
COST, SHARES = positions_store.get_lot(SYMBOL)

def rsi(close, window=14):
    delta = close.diff()
    up = delta.clip(lower=0).rolling(window).mean()
    down = -delta.clip(upper=0).rolling(window).mean()
    rs = up / down
    return 100 - (100 / (1 + rs))

def get_data():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="4mo", auto_adjust=False)
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
def judge(price, ma20, ma60, high60, rs14, vol=None, vol_ma20=None):
    if abs(ma20 - ma60) / ma60 <= 0.015 and abs(price - ma60) / ma60 <= 0.015 and abs(price - ma20) / ma20 <= 0.02:
        return f"⚪ {price} 均線糾結({ma20:.0f}/{ma60:.0f})、牛皮盤整 — 沒選邊前抱著、別追進追出;帶量站回 {ma60*(1+TOL):.0f} 才算轉強、帶量破 {ma20*(1-TOL):.0f} 才算轉弱。"
    if price < ma60 * (1 - TOL):
        return f"⚠️ {price} 跌破季線({ma60:.0f}) — 轉弱,留意減碼。"
    if price < ma20 * (1 - TOL):
        return f"🟡 {price} 跌破月線({ma20:.0f}) — 回檔,守季線({ma60:.0f})、可小撿。"
    if rs14 >= 70 and price >= high60 * 0.98:
        return f"🔴 {price} 過熱貼高(RSI {rs14:.0f}) — 可賣強鎖利。"
    if price >= high60 * 0.99:
        return f"🟢 {price} 創高({high60:.0f}) — 沒過熱續抱。"
    return f"⚪ {price} 健康多頭(月線 {ma20:.0f}上、RSI {rs14:.0f}) — 順勢抱,拉回 {ma20:.0f} 撐住可小撿。"

def run():
    price, ma20, ma60, high60, rs14, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) 健康多頭/順勢抱 ===")
    print(f"市價：{price}    月線：{ma20:.0f}    季線：{ma60:.0f}    季高：{high60:.0f}    RSI：{rs14:.0f}")
    print(f"成交量：{vdesc}")
    if SHARES:
        print(f"成本：{COST}（帳面 {(price/COST-1)*100:+.1f}%）    {SHARES} 股")
    else:
        print("空手")
    print(judge(price, ma20, ma60, high60, rs14))
    print(f"\n備忘：沒訊號就抱 / 拉回月線小撿 / RSI≥70貼高賣強 / 跌破季線留意（工業電腦龍頭）")

if __name__ == "__main__":
    run()
