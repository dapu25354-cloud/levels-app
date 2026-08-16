"""
中信金(2891) 金融核心/持有賣強 關卡監控
------------------------------------------------------------
背景:大型金控、健康多頭、貼近季高、RSI偏溫(跟元大金同組,金融這波漲多)。使用者沒空盯 -> 抱著就好。
策略:沒過熱就抱;真過熱貼高(RSI≥70)才像元大金那樣賣強鎖利一部分;跌破均線才留意。

關卡(均線即時算):
  過熱貼高(RSI≥70+近季高) = 可賣強鎖利一部分(同元大金邏輯)
  20MA上未過熱   = 健康多頭,抱著,沒訊號別賣
  跌破20MA       = 回檔,守60日線別慌
  跌破60MA       = 轉弱,減碼
"""
import sys
import yfinance as yf

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "2891.TW"
NAME = "中信金"

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
        return f"⚠️ {price} 跌破季線({ma60:.1f}) — 轉弱,減碼。"
    if price < ma20 * (1 - TOL):
        return f"🟡 {price} 跌破月線({ma20:.1f}) — 回檔,守季線({ma60:.1f})別慌。"
    if rs14 >= 70 and price >= high60 * 0.98:
        return f"🔴 {price} 過熱貼高(RSI {rs14:.0f}) — 可賣強鎖利一部分(同元大金邏輯)。"
    return (f"⚪ {price} 健康多頭(月線 {ma20:.1f}上、RSI {rs14:.0f}) — 抱著,沒過熱別賣。")

def run():
    price, ma20, ma60, high60, rs14, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) 金融核心/持有賣強 ===")
    print(f"市價：{price}    月線：{ma20:.1f}    季線：{ma60:.1f}    季高：{high60:.1f}    RSI：{rs14:.0f}")
    print(f"成交量：{vdesc}")
    print(judge(price, ma20, ma60, high60, rs14))
    print(f"\n備忘：RSI≥70貼高才賣強鎖利 / 月線上抱著 / 跌破月線別慌 / 跌破季線減碼")

if __name__ == "__main__":
    run()
