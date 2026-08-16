"""
聯鈞(3450) CPO/矽光子飆股 試單持有/弱接 關卡監控
------------------------------------------------------------
背景:CPO/矽光子一條龍(含源傑曝險、800G/1.6T),2026 主流題材飆股、波動大。
     從觀察區試單轉持有。
策略:試單小量先抱著看它跑;過熱貼高賣強鎖利;拉回均線可「小量」接(別追高、別往下大攤,留子彈);
     跌破60MA轉弱就停手/汰弱。同緯穎邏輯但這檔有正常均線可用。
成本/股數:見 app 內持倉管理(不寫死於程式碼)。

關卡(均線即時算):
  過熱貼高(RSI≥70+近季高) = 賣強鎖利一部分
  創高           = 沒過熱續抱、別賣飛
  20MA上未過熱   = 健康,抱著試單,拉回再小量接
  跌破20MA       = 回檔,守60日線、想加小量別追
  跌破60MA       = 轉弱,停手、試單別大攤
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "3450.TW"
NAME = "聯鈞"

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
        df = yf.Ticker("3450.TWO").history(period="4mo", auto_adjust=False)
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
        return f"⚠️ {price} 跌破季線({ma60:.0f}) — 轉弱,停手、試單別大攤。"
    if price < ma20 * (1 - TOL):
        return f"🟡 {price} 跌破月線({ma20:.0f}) — 回檔,守季線({ma60:.0f});想加小量、別追、別大攤。"
    if rs14 >= 70 and price >= high60 * 0.98:
        return f"🔴 {price} 過熱貼高(RSI {rs14:.0f}) — 賣強鎖利一部分(飆股震大、別賣飛核心)。"
    if price >= high60 * 0.99:
        return f"🟢 {price} 創高({high60:.0f}) — 沒過熱續抱、別賣飛。"
    return (f"⚪ {price} 健康(月線 {ma20:.0f}上、RSI {rs14:.0f}) — 抱著試單,"
            f"拉回 {ma20:.0f} 撐住可小量接、別追高。")

def run():
    price, ma20, ma60, high60, rs14, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) CPO/矽光子飆股 試單持有/弱接 ===")
    if SHARES:
        pnl = (price / COST - 1) * 100
        print(f"市價：{price}    成本：{COST}（帳面 {pnl:+.1f}%）    {SHARES} 股(試單)")
    else:
        print(f"市價：{price}    空手")
    print(f"月線：{ma20:.0f}    季線：{ma60:.0f}    季高：{high60:.0f}    RSI：{rs14:.0f}")
    print(f"成交量：{vdesc}")
    print(judge(price, ma20, ma60, high60, rs14))
    print(f"\n備忘：CPO飆股波動大、試單小量 / 過熱賣強別賣飛 / 拉回小量接別追別大攤 / 跌破季線停手")

if __name__ == "__main__":
    run()
