"""
世禾(3551) 健康多頭/順勢抱 關卡監控
------------------------------------------------------------
背景:溫和健康多頭(站穩均線、RSI不熱),半導體設備組裡唯一多頭。比較「悶」、不給戲劇訊號。
策略:沒訊號就抱;拉回20MA可小撿;真過熱才賣強;跌破60MA才留意。
成本/股數:見 app 內持倉管理(不寫死於程式碼,曾多次校正/加碼/減碼)。

關卡(均線即時算):
  過熱貼高(RSI≥70+近季高) = 可賣強(少見)
  創高           = 沒過熱續抱
  20MA上未過熱   = 健康溫和多頭,抱著順勢
  跌破20MA       = 回檔,守60日線、可小撿
  跌破60MA       = 轉弱,留意
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "3551.TWO"
NAME = "世禾"

# ====== 你的部位(app 內持倉管理可改) ======
COST, SHARES = positions_store.get_lot(SYMBOL)
# ============================================

def rsi(close, window=14):
    delta = close.diff()
    up = delta.clip(lower=0).rolling(window).mean()
    down = -delta.clip(upper=0).rolling(window).mean()
    rs = up / down
    return 100 - (100 / (1 + rs))

def get_data():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="4mo", auto_adjust=False)
    if df.empty:
        df = yf.Ticker("3551.TW").history(period="4mo", auto_adjust=False)
    c = df['Close']
    price = float(c.iloc[-1])
    ma20 = float(c.rolling(20).mean().iloc[-1])
    ma60 = float(c.rolling(60).mean().iloc[-1])
    high60 = float(c.iloc[-60:].max())
    rs14 = float(rsi(c).iloc[-1])
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            price = float(rp)
    except Exception:
        pass
    return price, ma20, ma60, high60, rs14

# 均線上下留 1% 緩衝:價要真的低於均線約 1% 才算「破」,不然只是貼線噪音,
# 避免像差不到 1 點就把「盤整」誤報成「轉弱」、害人追進追出。
TOL = 0.01

def judge(price, ma20, ma60, high60, rs14):
    # 均線糾結(20MA≈60MA)+ 價貼在附近 = 牛皮盤整,別追每天的強弱、別追進追出
    ma_tangle = abs(ma20 - ma60) / ma60 <= 0.015
    near_ma = abs(price - ma60) / ma60 <= 0.015 and abs(price - ma20) / ma20 <= 0.02
    if ma_tangle and near_ma:
        return (f"⚪ {price} 均線糾結({ma20:.0f}/{ma60:.0f})、牛皮盤整 — 在成本附近來回,"
                f"沒選邊前抱著就好,別追進追出。帶量站回 {ma60*(1+TOL):.0f} 才算轉強、"
                f"帶量破 {ma20*(1-TOL):.0f} 才算轉弱。")
    if price < ma60 * (1 - TOL):
        return f"⚠️ {price} 跌破60日線({ma60:.0f}) — 轉弱,留意、別再加。"
    if price < ma20 * (1 - TOL):
        return f"🟡 {price} 跌破20日線({ma20:.0f}) — 回檔,守60日線({ma60:.0f})、可小撿。"
    if rs14 >= 70 and price >= high60 * 0.98:
        return f"🔴 {price} 過熱貼高(RSI {rs14:.0f}) — 可賣強鎖利(它少見過熱)。"
    if price >= high60 * 0.99:
        return f"🟢 {price} 創高({high60:.0f}) — 沒過熱續抱。"
    return (f"⚪ {price} 健康溫和多頭(20MA {ma20:.0f}上、RSI {rs14:.0f}) — 抱著順勢,"
            f"拉回 {ma20:.0f} 撐住可小撿。")

def run():
    price, ma20, ma60, high60, rs14 = get_data()
    print(f"=== {NAME}({SYMBOL}) 健康多頭/順勢抱 ===")
    if SHARES:
        pnl = (price / COST - 1) * 100
        print(f"市價：{price}    成本：{COST}（帳面 {pnl:+.1f}%）    {SHARES} 股")
    else:
        print(f"市價：{price}    空手")
    print(f"20日線：{ma20:.0f}    60日線：{ma60:.0f}    季高：{high60:.0f}    RSI：{rs14:.0f}")
    print(judge(price, ma20, ma60, high60, rs14))
    print(f"\n備忘：均線糾結時抱著別追進追出 / 設備組裡唯一多頭")

if __name__ == "__main__":
    run()
